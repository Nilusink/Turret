import io
import socket
import struct
import time

import cv2
import numpy as np
import math


# camera setup
VERTICAL_FOV: float = math.radians(41.41)
HORIZONTAL_FOV: float = math.radians(53.5)

# Set up a socket server on port 8000
server_socket = socket.socket()
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(('0.0.0.0', 8000))
server_socket.listen(0)

# Define the range of red color in HSV
lower_red1 = np.array([0, 50, 50])
upper_red1 = np.array([10, 255, 255])


lower_red2 = np.array([170, 50, 50])
upper_red2 = np.array([180, 255, 255])

# Load the classifier
classifier = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

# Accept a single connection and make a file-like object out of it
connection = server_socket.accept()[0].makefile('rwb')
print("connected")


def pixel_to_angle(y, image_height, fov, mount_angle):
    cy = image_height / 2
    theta = math.atan((y - cy) * math.tan(fov/2) / cy)
    return math.degrees(theta + mount_angle)


def process_image(img) -> tuple[bool, int, int]:
    image_height, image_width = img.shape[:2]

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Detect objects using the classifier
    objects = classifier.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
        )

    # Draw a rectangle around each detected object
    highest_weight: float = -1
    biggest_center: tuple[int, int] = (-1, -1)

    for (x, y, w, h) in objects:
        area = w * h
        weight = area + (y > image_height / 2) * (image_width *
                                                  image_height) / 4

        if weight > highest_weight:
            highest_weight = weight
            biggest_center = x + w/2, y + h/2

        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)

    cv2.circle(img, (int(image_width / 2), int(image_height / 2)), 4, (0, 0, 255), 1)

    if highest_weight == -1:
        return False, 0, 0

    theta1 = pixel_to_angle(biggest_center[1], image_height, VERTICAL_FOV, 0)
    theta2 = pixel_to_angle(biggest_center[0], image_width, HORIZONTAL_FOV, 0)

    return True, int(4096 * (theta1 / 360)), int(4096 * (theta2 / 360))


def process_red(img):
    hsv = cv2.cvtColor(cv2.UMat(img), cv2.COLOR_BGR2HSV)

    # mask stuff
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)

    # Create cv2.UMat objects from numpy arrays
    mask1_umat = cv2.UMat(mask1)
    mask2_umat = cv2.UMat(mask2)

    # Combine the masks
    mask_umat = cv2.bitwise_or(mask1_umat, mask2_umat)

    # Convert the cv2.UMat object back to numpy array
    mask = mask_umat.get()

    # Apply morphology operations to remove noise
    kernel = np.ones((5,5), np.uint8)
    mask = cv2.erode(mask, kernel, iterations=1)
    mask = cv2.dilate(mask, kernel, iterations=1)


    # Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Get the largest contour, which should correspond to the red circle
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        (x,y), radius = cv2.minEnclosingCircle(largest_contour)
        center = (int(x), int(y))
        radius = int(radius)

        # circle to small
        if radius < 20:
            return 0, 0

        else:
            # Draw the circle and its center
            cv2.circle(img, center, radius, (0, 255, 0), 2)
            cv2.circle(img, center, 5, (0, 0, 255), -1)

            # set direction
            image_height, image_width = img.shape[:2]
            fov = math.radians(60)  # Vertical field of view in radians

            theta1 = pixel_to_angle(center[1], image_height, fov, 0)
            theta2 = pixel_to_angle(center[0], image_width, fov, 0)

            return int(4096 * (theta1 / 360)), int(4096 * (theta2 / 360))

    return 0, 0


try:
    cv2.namedWindow('Image', cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Image", (1000, 700))

    print("starting to receive\n")
    while True:
        # Read the length of the image as a 32-bit unsigned int
        image_len = struct.unpack('<L', connection.read(struct.calcsize('<L')))[0]
        print("got image")

        # Construct a stream to hold the image data and read the image data from the connection
        image_stream = io.BytesIO()
        image_stream.write(connection.read(image_len))

        # Rewind the stream and convert the image data to a NumPy array
        image_stream.seek(0)
        image_array = np.frombuffer(image_stream.getvalue(), dtype=np.uint8)

        # Decode the image and display it
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        start = time.perf_counter()
        target_found, off_y, off_x = process_image(image)
        took = (time.perf_counter() - start) * 1000

        print(f"\rtook {took:.2f}ms", end="", flush=True)

        cv2.imshow('Image', image)
        cv2.waitKey(1)

        # Send an integer back to the Raspberry Pi
        connection.write(struct.pack('<i', target_found))
        connection.write(struct.pack('<i', off_y))
        connection.write(struct.pack('<i', off_x))
        connection.flush()

finally:
    connection.close()
    server_socket.close()
