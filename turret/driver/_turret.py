"""
_turret.py
13. July 2023

combines the two stepper motors

Author:
Nilusink
"""
from ._stepper import Stepper
from ._pinout import X_MOTOR_PINS, Y_MOTOR_PINS


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

    def cleanup(self) -> None:
        self.x_stepper.cleanup()
        self.y_stepper.cleanup()
