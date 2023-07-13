"""
_client.py
13. July 2023

<description>

Author:
Nilusink
"""
from concurrent.futures import ThreadPoolExecutor
from ..imager import Imager
import typing as tp
import socket
import struct


class Client:
    running: bool = True

    def __init__(
            self,
            imager: Imager,
            host: str,
            image_port: int = 8000,
            control_port: int = 8001
    ) -> None:
        self._imager = imager

        self._host = host
        self._image_port = image_port
        self._control_port = control_port

        self._image_socket = socket.socket()
        self._control_socket = socket.socket()

        # threading
        self._pool = ThreadPoolExecutor(max_workers=2)

    def _run_image(self) -> None:
        connection = self._image_socket.makefile("rwb")

        try:
            while self.running:
                # send image size and image
                size, image = self._imager.get_image()
                connection.write(struct.pack("<L", size))
                connection.flush()
                connection.write(image)

                # wait for the servers response
                struct.unpack("<i", connection.read(struct.calcsize("<i")))

        except IOError:
            self.close()

    def run(self) -> None:
        """
        connects to the server and runs all threads
        """
        self._image_socket.connect((self._host, self._image_port))
        self._control_socket.connect((self._host, self._control_port))

        # start threads and wait for them to finish
        self._pool.submit(self._run_image)
        self._pool.shutdown()

    def close(self) -> None:
        """
        shutdown the client
        """
        self._image_socket.close()
        self._control_socket.close()
        self.running = False
