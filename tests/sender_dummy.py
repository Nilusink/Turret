import cv2
import socket
import struct
import time

CAM_RESOLUTION = (1200, 800)
# Connect a client socket to the server's IP address and port
client_socket = socket.socket()
client_socket.connect(('127.0.0.1', 8000))

# Make a file-like object out of the connection
connection = client_socket.makefile('rwb')

try:
    # Initialize the USB camera
    camera = cv2.VideoCapture(0)  # Replace 0 with the appropriate camera index if multiple cameras are connected
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_RESOLUTION[0])
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_RESOLUTION[1])

    # Allow the camera to warm up
    time.sleep(2)

    while True:
        # Capture a frame from the camera
        ret, frame = camera.read()
        if not ret:
            break

        # Convert the frame to JPEG format
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
        _, image = cv2.imencode('.jpeg', frame, encode_param)

        # Send the image length and data over the network
        connection.write(struct.pack('<L', len(image)))
        connection.flush()
        connection.write(image.tobytes())
        connection.flush()

        # # Receive an integer from the server
        target_found = struct.unpack('<i', connection.read(struct.calcsize('<i')))[0]
        off_y = struct.unpack('<i', connection.read(struct.calcsize('<i')))[0]
        off_x = struct.unpack('<i', connection.read(struct.calcsize('<i')))[0]

finally:
    connection.close()
    client_socket.close()

    # Release the camera
    camera.release()

    time.sleep(5)

    exit(1)
