"""
_server.py
12. July 2023

<description>

Author:
Nilusink
"""
import typing as tp
import numpy as np
import socket
import struct
import time
import cv2
import io


class Server:
    running: bool = True

    def __init__(
            self,
            image_callback: tp.Callable[[np.ndarray], tp.Tuple[bool, int, int]],
            port: int = 8000,
            host: str = "0.0.0.0",
            show_image: bool = False
    ) -> None:
        self._callback = image_callback
        self.show_image = show_image

        self._socket = socket.socket()
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind((host, port))
        self._socket.listen()

    def run(self) -> None:
        """
        run the server
        """
        connection = self._socket.accept()[0].makefile("rwb")

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
            target_found, off_y, off_x = self._callback(image)
            took = (time.perf_counter() - start) * 1000

            # Send an integer back to the Raspberry Pi
            connection.write(struct.pack('<i', target_found))
            connection.write(struct.pack('<i', off_y))
            connection.write(struct.pack('<i', off_x))
            connection.flush()

            print(f"\rtook {took:.2f}ms", end="", flush=True)

            if self.show_image:
                cv2.imshow('Image', image)
                cv2.waitKey(1)
