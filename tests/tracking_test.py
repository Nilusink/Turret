import cv2

# Initialize the video stream
stream = cv2.VideoCapture(0)  # Replace with your video stream source

# Define the initial bounding box of the object to track
initial_bbox = None
tracking = False

# Create an object tracker (e.g., KCF tracker)
tracker = cv2.TrackerCSRT_create()

while True:
    # Capture frame from the video stream
    ret, frame = stream.read()
    if not ret:
        break



    # Preprocess the frame if necessary (e.g., resize, convert color space, apply filters)

    # Pick an object to track (e.g., using mouse events)
    if not tracking:
        cv2.imshow('Frame', frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('p'):
            bbox = cv2.selectROI('Frame', frame, fromCenter=False, showCrosshair=True)
            print(bbox, frame.shape)
            initial_bbox = bbox
            print(1)
            tracker.init(frame, bbox)
            print(2)
            tracking = True

    # Track the object
    if tracking:
        success, bbox = tracker.update(frame)
        if success:
            # Draw bounding box on the frame
            (x, y, w, h) = [int(v) for v in bbox]
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    # Display the frame
    cv2.imshow('Frame', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the video stream and close windows
stream.release()
cv2.destroyAllWindows()
