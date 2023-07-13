"""
_server.py
12. July 2023

<description>

Author:
Nilusink
"""
from concurrent.futures import ThreadPoolExecutor
import typing as tp
import numpy as np
import socket
import struct
import time
import io

try:
    import cv2
    OPENCV = True

except ImportError:
    OPENCV = False


class Server:
    running: bool = True

    def __new__(cls, *args, **kwargs):
        if not OPENCV:
            raise RuntimeError("opencv module is not installed!")

        return object.__new__(cls)

    def __init__(
            self,
            image_callback: tp.Callable[[np.ndarray], tp.Tuple[bool, int, int]],
            image_port: int = 8000,
            control_port: int = 8001,
            host: str = "0.0.0.0",
            show_image: bool = False
    ) -> None:
        self._callback = image_callback
        self.show_image = show_image

        # socket setup
        self._image_socket = socket.socket()
        self._image_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._image_socket.bind((host, image_port))
        self._image_socket.listen()

        self._control_socket = socket.socket()
        self._control_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._control_socket.bind((host, control_port))
        self._control_socket.listen()

        # threading
        self._pool = ThreadPoolExecutor(max_workers=2)

    def _run_image(self, connection: io.BufferedRWPair) -> None:
        """
        run the server
        """
        while self.running:
            # Read the length of the image as a 32-bit unsigned int
            image_len = struct.unpack('<L', connection.read(struct.calcsize('<L')))[0]

            # Construct a stream to hold the image data and read the image data from the connection
            image_stream = io.BytesIO()
            image_stream.write(connection.read(image_len))

            # Rewind the stream and convert the image data to a NumPy array
            image_stream.seek(0)
            image_array = np.frombuffer(image_stream.getvalue(), dtype=np.uint8)

            # Decode the image and display it
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

            start = time.perf_counter()
            self._callback(image)
            took = (time.perf_counter() - start) * 1000

            # Send an integer back to the Raspberry Pi
            connection.flush()

            print(f"\rImage took {took:.2f}ms", end="", flush=True)

            if self.show_image:
                cv2.imshow('Image', image)
                cv2.waitKey(1)

        # close socket if loop finished
        connection.close()

    def _run_control(self, connection: io.BufferedRWPair) -> None:
        """
        controls the turret movement
        """
        # connection.write(struct.pack('<i', target_found))
        # connection.write(struct.pack('<i', off_y))
        # connection.write(struct.pack('<i', off_x))
        #
        # # close socket if loop finished
        # connection.close()

    def run(self) -> None:
        """
        run image and control threads
        :return:
        :rtype:
        """
        image_connection = self._image_socket.accept()[0].makefile("rwb")
        control_connection = self._control_socket.accept()[0].makefile("rwb")

        self._pool.submit(self._run_image, image_connection)
        # self._pool.submit(self._run_control, control_connection)

        # wait for both threads to exit
        self._pool.shutdown()

    def close(self) -> None:
        """
        shuts down the server
        """
        self._image_socket.close()
        self._control_socket.close()
        self.running = False
