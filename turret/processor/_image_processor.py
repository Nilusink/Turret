"""
_image_processor.py
24. April 2023

Detects Threads in the image

Author:
Nilusink
"""
from ._target_classifier import TargetClassifier
from ._image_tools import pixel_to_angle
import typing as tp
import numpy as np
import math
import cv2


class CameraConfiguration(tp.TypedDict):
    vertical_fov: float
    horizontal_fov: float


class ImageProcessor:
    _classifier: TargetClassifier = ...
    _cam_config: CameraConfiguration = ...
    _detection_classifier = ...

    def __init__(
            self,
            cam_config: CameraConfiguration = ...,
            detection_classifier=...
    ) -> None:
        self._classifier = TargetClassifier()

        self._cam_config = cam_config
        if cam_config is ...:
            # default picamera configuration
            self._cam_config = CameraConfiguration(
                vertical_fov=math.radians(41.41),
                horizontal_fov=math.radians(53.5)
            )

        self._detection_classifier = detection_classifier
        if detection_classifier is ...:
            self._detection_classifier = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )

    def process_image(self, img: np.ndarray):
        # get image dimensions
        image_height, image_width = img.shape[:2]

        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Detect objects using the classifier
        objects = self._detection_classifier.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
        )

        # Draw a rectangle around each detected object
        highest_weight: float = -1
        biggest_center: tuple[int, int] = (-1, -1)

        # self._classifier.update_record(objects)
        for (x, y, w, h) in objects:
            area = w * h
            weight = area + (y > image_height / 2) * (
                        image_width * image_height) / 4

            if weight > highest_weight:
                highest_weight = weight
                biggest_center = x + w / 2, y + h / 2

            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)

        if highest_weight == -1:
            return False, 0, 0

        theta1 = pixel_to_angle(
            biggest_center[1],
            image_height,
            self._cam_config["vertical_fov"],
            0
            )
        theta2 = pixel_to_angle(
            biggest_center[0],
            image_width,
            self._cam_config["horizontal_fov"],
            0
            )

        return True, int(4096 * (theta1 / 360)), int(4096 * (theta2 / 360))

