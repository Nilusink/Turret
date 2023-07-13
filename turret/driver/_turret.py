"""
_turret.py
13. July 2023

combines the two stepper motors

Author:
Nilusink
"""
from ._pinout import X_MOTOR_PINS, Y_MOTOR_PINS
from ._stepper import Stepper
import time


class Turret:
    def __init__(self) -> None:
        self.x_stepper = Stepper(X_MOTOR_PINS)
        self.y_stepper = Stepper(Y_MOTOR_PINS)

    def move_steps(self, x: int, y: int) -> None:
        self.x_stepper.step(x)
        self.y_stepper.step(y)

    def move_steps_from_current(self, x: int, y: int) -> None:
        self.x_stepper.step_from_current(x)
        self.y_stepper.step_from_current(y)

    def move_velocity(self, x: float, y: float) -> None:
        self.x_stepper.move_at_speed(x)
        self.y_stepper.move_at_speed(y)

    def stop(self) -> None:
        self.x_stepper.stop()
        self.y_stepper.stop()

    def resume(self) -> None:
        self.x_stepper.resume()
        self.y_stepper.resume()

    def reset_tracking(self) -> None:
        self.x_stepper.reset_tracking()
        self.y_stepper.reset_tracking()

    def is_done(self) -> bool:
        return self.x_stepper.is_done() and self.y_stepper.is_done()

    def wait_for_step(self) -> None:
        """
        waits until the stepper has reached its target
        """
        while not self.is_done():
            time.sleep(.01)

    def cleanup(self) -> None:
        self.x_stepper.cleanup()
        self.y_stepper.cleanup()
