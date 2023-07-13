"""
_imager.py
13. July 2023

<description>

Author:
Nilusink
"""
from picamera import PiCamera
import io


class Imager:
    def __init__(
            self,
            camera_resolution: tuple[int, int],
            framerate: int
    ) -> None:
        self._cam = PiCamera()
        self._cam.resolution = camera_resolution
        self._cam.framerate = framerate

        self._stream = io.BytesIO()
        self._capture = self._cam.capture_continuous(self._stream, 'jpeg', use_vieo_port=True)

    def get_image(self) -> tuple[int, bytes]:
        # update capture
        self._capture.next()

        # get size
        size = self._stream.tell()

        # get image
        self._stream.seek(0)
        image = self._stream.read()
        self._stream.seek(0)
        self._stream.truncate()

        return size, image
