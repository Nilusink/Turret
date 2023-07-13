"""
_client.py
13. July 2023

<description>

Author:
Nilusink
"""
from concurrent.futures import ThreadPoolExecutor
from ..debugging import print_traceback
from ..imager import Imager
import typing as tp
import socket
import struct
import json


class Client:
    running: bool = True

    def __init__(
            self,
            imager: Imager,
            control_callback: tp.Callable[[dict], tp.Any],
            host: str,
            image_port: int = 8000,
            control_port: int = 8001
    ) -> None:
        self._imager = imager

        self._host = host
        self._image_port = image_port
        self._control_port = control_port
        self._control_callback = control_callback

        self._image_socket = socket.socket()
        self._control_socket = socket.socket()

        # threading
        self._pool = ThreadPoolExecutor(max_workers=2)

    @print_traceback(print)
    def _run_image(self) -> None:
        connection = self._image_socket.makefile("rwb")

        while self.running:
            # send image size and image
            size, image = self._imager.get_image()
            connection.write(struct.pack("<L", size))
            connection.flush()
            connection.write(image)

            # wait for the servers response
            struct.unpack("<i", connection.read(struct.calcsize("<i")))

        self.close()

    @print_traceback(print)
    def _run_control(self) -> None:
        connection = self._control_socket.makefile("rwb")

        while self.running:
            message_len = struct.unpack("<L", connection.read(struct.calcsize("<L")))[0]
            message = connection.read(message_len).decode()

            data = json.loads(message)
            self._control_callback(data)

    def run(self) -> None:
        """
        connects to the server and runs all threads
        """
        self._image_socket.connect((self._host, self._image_port))
        self._control_socket.connect((self._host, self._control_port))

        # start threads and wait for them to finish
        self._pool.submit(self._run_image)
        self._pool.submit(self._run_control)
        self._pool.shutdown()

    def close(self) -> None:
        """
        shutdown the client
        """
        self._image_socket.close()
        self._control_socket.close()
        self.running = False
