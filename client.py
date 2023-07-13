"""
client.py
13. July 2023

<description>

Author:
Nilusink
"""
from turret.stream import Client
from turret.imager import Imager
from turret.driver import Turret


turret = Turret()


def control_callback(data) -> None:
    x, y = data["x"], data["y"]

    if data["mode"] == "off":  # offset
        turret.move_steps_from_current(x, y)

    elif data["mode"] == "vel":  # velocity
        if abs(x) < .1 or abs(y) < .1:
            turret.stop()

        else:
            turret.move_velocity(x, y)

    else:
        print(f"Invalid mode: {data['mode']}")


if __name__ == "__main__":
    imager = Imager((1200, 800), 32)
    client = Client(
        imager,
        control_callback,
        "127.0.0.1"
    )
    client.run()
    turret.cleanup()
