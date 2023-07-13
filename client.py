"""
client.py
13. July 2023

<description>

Author:
Nilusink
"""
from turret.stream import Client
from turret.imager import Imager


if __name__ == "__main__":
    imager = Imager((1200, 800), 32)
    client = Client(imager, "127.0.0.1")
