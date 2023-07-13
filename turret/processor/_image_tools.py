"""
_image_tools.py
24. April 2023

<description>

Author:
Nilusink
"""
import numpy as np
import math

try:
    import cv2
    OPENCV = True

except ImportError:
    OPENCV = False


def pixel_to_angle(y, image_height, fov, mount_angle):
    cy = image_height / 2
    theta = math.atan((y - cy) * math.tan(fov/2) / cy)
    return math.degrees(theta + mount_angle)


def sharpen_image(image: np.ndarray) -> np.ndarray:
    """
    sharpen an image (in form of a np.ndarray)
    :param image: input image
    :return: processed image
    """
    if not OPENCV:
        raise RuntimeError("opencv module is not installed!")

    # Define the kernel for sharpening
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])

    # Apply the kernel to the input image
    sharpened_image = cv2.filter2D(image, -1, kernel)

    return sharpened_image
