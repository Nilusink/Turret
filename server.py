"""
server.pg
12. July 2023

<description>

Author:
Nilusink
"""
from turret.processor import pixel_to_angle, CameraConfiguration, sharpen_image
from turret.debugging import print_traceback
from turret.stream import Server
# from turret.processor import ImageProcessor
import pygame as pg
import numpy as np
import math
import cv2


pg.init()
pg.joystick.init()


TRACKER = cv2.TrackerCSRT_create


class Controller:
    def __init__(self) -> None:
        self._designator_size = 50
        self._designator_speed = 500
        self._max_designator_speed = 500
        self._last_buttons: tuple[bool, bool, bool, bool, bool] = (False, False, False, False, False)

        self._cam_config = CameraConfiguration(
            vertical_fov=math.radians(41.41),
            horizontal_fov=math.radians(53.5)
        )

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

        # tracker setup
        self.tracker = TRACKER()

        # server setup
        self._server = Server(self.on_image, show_image=False)
        self._server.run()

    @print_traceback(print)
    def _pg_loop(self) -> None:
        track = False
        while self._server.running:
            # handle events
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    exit(0)

            # read joystick
            x = self.throttle.get_axis(0)
            y = self.throttle.get_axis(1)
            target = self.throttle.get_button(5)

            up = self.throttle.get_button(6)
            fw = self.throttle.get_button(7)
            down = self.throttle.get_button(8)
            back = self.throttle.get_button(9)

            # designator size
            if up:
                self._designator_size += 10

            elif down:
                if self._designator_size > 10:
                    self._designator_size -= 10

            # designator speed
            if back:
                if self._designator_speed < self._max_designator_speed:
                    self._designator_speed += self._max_designator_speed / 50

            elif fw:
                if self._designator_speed > 1:
                    self._designator_speed -= self._max_designator_speed / 50

            # get image size
            image_height, image_width, _ = self.last_image.shape

            # zoom
            x_zoom = int(((self._max_designator_speed - self._designator_speed) / 1500) * image_width)
            y_zoom = int(((self._max_designator_speed - self._designator_speed) / 1500) * image_height)
            img = self.last_image[
                y_zoom:image_height - y_zoom,
                x_zoom:image_width - x_zoom
            ]
            img = cv2.resize(img, (image_width, image_height))

            # convert self.last_image to pg surface
            opencv_image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            opencv_image_rotated = np.rot90(opencv_image)

            # Copy the resized image data to the Pygame surface
            self.surface_image = pg.surfarray.make_surface(opencv_image_rotated)

            # fill background with image
            self.surf.blit(self.surface_image, (0, 0))

            if target and not self._last_buttons[0]:
                if track:
                    self.tracker = TRACKER()
                    track = False

                else:
                    bbox = [
                        int(image_width / 2) - int(self._designator_size / 2),
                        int(image_height / 2) - int(self._designator_size / 2),
                        self._designator_size,
                        self._designator_size
                    ]
                    print(bbox, img.shape)
                    self.tracker.init(img, bbox)
                    track = True

            if track:
                success, bbox = self.tracker.update(img)
                theta1 = 0
                theta2 = 0
                if success:
                    # Draw bounding box on the frame
                    (bx, by, w, h) = [int(v) for v in bbox]

                    # pg.draw.rect(
                    #     self.surf,
                    #     (255, 0, 0, 1),
                    #     pg.rect.Rect(
                    #         image_width - bx - w,
                    #         by,
                    #         w,
                    #         h
                    #     ),
                    #     width=2
                    # )

                    pg.draw.circle(
                        self.surf,
                        (255, 0, 0, 1),
                        (image_width - bx - w / 2, by + h / 2),
                        5
                    )
                    pg.draw.line(
                        self.surf,
                        (255, 0, 0, 1),
                        (image_width / 2, image_height / 2),
                        (image_width - bx - w / 2, by + h / 2),
                        2
                    )

                    theta1 = pixel_to_angle(
                        by + h / 2,
                        image_height,
                        self._cam_config["vertical_fov"],
                        0
                    )
                    theta2 = pixel_to_angle(
                        bx + w / 2,
                        image_width,
                        self._cam_config["horizontal_fov"],
                        0
                    )

                y_off, x_off = int(4096 * (theta1 / 360)), int(4096 * (theta2 / 360))
                self._server.send_command({
                    "mode": "off",
                    "x": -x_off,
                    "y": y_off
                })

            else:
                y *= self._designator_speed if abs(y) > .01 else 0
                x *= self._designator_speed if abs(x) > .01 else 0

                self._server.send_command({
                    "mode": "vel",
                    "x": x,
                    "y": y
                })

            # draw designator
            if track:
                pg.draw.line(  # top line
                    self.surf,
                    (0, 0, 0, 1),
                    (image_width / 2, image_height / 2 - self._designator_size),
                    (image_width / 2, image_height / 2 - self._designator_size / 2),
                    width=4
                )
                pg.draw.line(  # right line
                    self.surf,
                    (0, 0, 0, 1),
                    (image_width / 2 + self._designator_size / 2, image_height / 2),
                    (image_width / 2 + self._designator_size, image_height / 2),
                    width=4
                )
                pg.draw.line(  # bottom line
                    self.surf,
                    (0, 0, 0, 1),
                    (image_width / 2, image_height / 2 + self._designator_size / 2),
                    (image_width / 2, image_height / 2 + self._designator_size),
                    width=4
                )
                pg.draw.line(  # right line
                    self.surf,
                    (0, 0, 0, 1),
                    (image_width / 2 - self._designator_size, image_height / 2),
                    (image_width / 2 - self._designator_size / 2, image_height / 2),
                    width=4
                )

            else:
                pg.draw.rect(self.surf, (0, 0, 0, 1), pg.rect.Rect(
                    (image_width / 2) - int(self._designator_size / 2),
                    (image_height / 2) - int(self._designator_size / 2),
                    self._designator_size,
                    self._designator_size
                ), width=4)

            # draw speed / zoom indicator
            pg.draw.line(
                self.surf,
                (0, 0, 0, 1),
                (40, 20),
                (40, 220),
                width=3
            )
            y_pos = 20 + self._designator_speed / self._max_designator_speed * 200
            pg.draw.line(
                self.surf,
                (0, 0, 0, 1),
                (20, y_pos),
                (60, y_pos),
                width=3
            )

            pg.display.flip()
            self._clock.tick(32)

            self._last_buttons = (target, up, fw, down, back)

    def run(self) -> None:
        self._server.pool.submit(self._pg_loop)
        self._server.wait_for_threads()

    def on_image(self, image: np.ndarray) -> None:
        image = cv2.flip(image, 1)
        self.last_image = image


if __name__ == "__main__":
    # t = ImageProcessor()

    c = Controller()
    c.run()
