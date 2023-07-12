"""
_image_tools.py
24. April 2023

<description>

Author:
Nilusink
"""
import math


def pixel_to_angle(y, image_height, fov, mount_angle):
    cy = image_height / 2
    theta = math.atan((y - cy) * math.tan(fov/2) / cy)
    return math.degrees(theta + mount_angle)
