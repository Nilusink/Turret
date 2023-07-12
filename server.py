"""
server.pg
12. July 2023

<description>

Author:
Nilusink
"""
from turret.stream import Server
# from turret.processor import ImageProcessor
import pygame as pg
import numpy as np
import cv2

pg.init()
pg.joystick.init()
surf = pg.display.set_mode((1280, 720), flags=pg.RESIZABLE)

throttle = None

for i in range(pg.joystick.get_count()):
    joystick = pg.joystick.Joystick(i)
    joystick.init()

    if "Throttle" in joystick.get_name():
        print(f"Selected: {joystick.get_name()}")
        throttle = joystick

if throttle is None:
    raise RuntimeError("Throttle is not available")


class Designator:
    max_speed = 30

    def __init__(self, width: int, height: int, size: int = 10) -> None:
        self.x = int(width / 2)
        self.y = int(height / 2)

        self._max_width = width
        self._max_height = height

        self.size = size

    @property
    def position(self) -> tuple[int, int]:
        return self.x, self.y

    def move(self, x: float, y: float) -> None:
        """
        :param x: -1 to 1
        :param y: -1 to 1
        """
        max_add = min(self._max_height, self._max_width) / self.max_speed
        x_add = max_add * x
        y_add = max_add * y

        if abs(x) > .1:
            res = self.x + x_add
            if self.size / 2 < res < self._max_width - self.size / 2:
                self.x += x_add

            elif res < self.size / 2:
                self.x = int(self.size / 2)

            else:
                self.x = self._max_width - int(self.size / 2)

        if abs(y) > .01:
            res = self.y + y_add
            if self.size / 2 < res < self._max_height - self.size / 2:
                self.y += y_add

            elif res < self.size / 2:
                self.y = int(self.size / 2)

            else:
                self.y = self._max_height - int(self.size / 2)


designator = Designator(1280, 720, 50)


def on_image(image):
    # convert image to pg surface
    opencv_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    opencv_image_rotated = np.rot90(opencv_image)

    # Copy the resized image data to the Pygame surface
    surface_image = pg.surfarray.make_surface(opencv_image_rotated)

    # handle events
    for event in pg.event.get():
        if event.type == pg.QUIT:
            exit(0)

    pg.event.pump()

    # fill background with image
    surf.fill((0, 0, 0, 0))
    surf.blit(surface_image, (0, 0))

    # read joystick
    x = throttle.get_axis(0)
    y = throttle.get_axis(1)
    target = throttle.get_button(5)

    up = throttle.get_button(6)
    fw = throttle.get_button(7)
    down = throttle.get_button(8)
    back = throttle.get_button(9)

    print(x, y, target, up, fw, down, back)
    designator.move(x, y)

    if up:
        designator.size += 10

    elif down:
        if designator.size > 10:
            designator.size -= 10

    if target:
        detection_object = image[
                           int(designator.y)-int(designator.size / 2):int(designator.y)+int(designator.size / 2),
                           int(1280 - designator.x)-int(designator.size / 2):int(1280 - designator.x)+int(designator.size / 2)
                           ]
        cv2.imwrite("tmp.png", cv2.flip(detection_object, 1))

    pg.draw.rect(surf, (0, 0, 0, 1), pg.rect.Rect(
        designator.x - int(designator.size / 2),
        designator.y - int(designator.size / 2),
        designator.size,
        designator.size
    ), width=4)

    pg.display.flip()

    return True, 0, 0


if __name__ == "__main__":
    # t = ImageProcessor()

    s = Server(on_image, show_image=False)
    s.run()
