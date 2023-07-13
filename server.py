"""
server.pg
12. July 2023

<description>

Author:
Nilusink
"""
from turret.debugging import print_traceback
from turret.stream import Server
# from turret.processor import ImageProcessor
import pygame as pg
import numpy as np
import cv2


pg.init()
pg.joystick.init()


class Controller:
    def __init__(self) -> None:
        self._designator_size = 50

        size = (1280, 720)
        self.surf = pg.display.set_mode(size, flags=pg.RESIZABLE)
        self._clock = pg.time.Clock()

        # try to find the throttle
        self.throttle = None
        for i in range(pg.joystick.get_count()):
            joystick = pg.joystick.Joystick(i)
            joystick.init()

            if "Throttle" in joystick.get_name():
                print(f"Selected: {joystick.get_name()}")
                self.throttle = joystick

        if self.throttle is None:
            raise RuntimeError("Throttle is not available")

        # initial images
        self.surface_image = pg.Surface(size)
        self.last_image = np.empty((*size, 3), dtype=np.uint8)

        # server setup
        self._server = Server(self.on_image, show_image=False)
        self._server.run()

    @print_traceback(print)
    def _pg_loop(self) -> None:
        while self._server.running:
            # handle events
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    exit(0)

            # fill background with image
            self.surf.fill((0, 0, 0, 0))
            self.surf.blit(self.surface_image, (0, 0))

            # read joystick
            x = self.throttle.get_axis(0)
            y = self.throttle.get_axis(1)
            target = self.throttle.get_button(5)

            up = self.throttle.get_button(6)
            fw = self.throttle.get_button(7)
            down = self.throttle.get_button(8)
            back = self.throttle.get_button(9)

            # get image size
            image_height, image_width, _ = self.last_image.shape

            if up:
                self._designator_size += 10

            elif down:
                if self._designator_size > 10:
                    self._designator_size -= 10

            if target:
                detection_object = self.last_image[
                                   int(image_height / 2) - int(self._designator_size / 2)
                                   :int(image_height / 2) + int(self._designator_size / 2),
                                   int(image_width / 2) - int(self._designator_size / 2)
                                   :int(image_width / 2) + int(self._designator_size / 2)
                                   ]
                cv2.imwrite("tmp.png", cv2.flip(detection_object, 1))

            pg.draw.rect(self.surf, (0, 0, 0, 1), pg.rect.Rect(
                image_width - int(self._designator_size / 2),
                image_height - int(self._designator_size / 2),
                self._designator_size,
                self._designator_size
            ), width=4)

            pg.display.flip()

            y *= 50 if abs(y) > .01 else 0
            x *= 50 if abs(x) > .01 else 0

            self._server.send_command({
                "mode": "off",
                "x": x,
                "y": y
            })
            self._clock.tick(60)

    def run(self) -> None:
        self._server.pool.submit(self._pg_loop)
        self._server.wait_for_threads()

    def on_image(self, image: np.ndarray) -> None:
        self.last_image = cv2.flip(image, 1)

        # convert self.last_image to pg surface
        opencv_image = cv2.cvtColor(self.last_image, cv2.COLOR_BGR2RGB)
        opencv_image_rotated = np.rot90(opencv_image)

        # Copy the resized image data to the Pygame surface
        self.surface_image = pg.surfarray.make_surface(opencv_image_rotated)


if __name__ == "__main__":
    # t = ImageProcessor()

    c = Controller()
    c.run()
