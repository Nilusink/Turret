"""
_stepper.py
13. July 2023

A base stepper motor driver

Author:
Nilusink
"""
from concurrent.futures import ThreadPoolExecutor
import typing as tp
import time

try:
    import RP.GPIO as GPIO
    PIGPIO = True

except ImportError:
    PIGPIO = False


STEP_SEQUENCE = [
    [1, 0, 0, 1],
    [1, 0, 0, 0],
    [1, 1, 0, 0],
    [0, 1, 0, 0],
    [0, 1, 1, 0],
    [0, 0, 1, 0],
    [0, 0, 1, 1],
    [0, 0, 0, 1]
]


class Stepper:
    running = True
    _gpio_initialized = False

    def __new__(cls, *args, **kwargs):
        if not PIGPIO:
            raise RuntimeError("RPi.GPIO module is not installed!")

        # check GPIO initialization
        if not cls._gpio_initialized:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)

            cls._gpio_initialized = True

        return object.__new__(cls)

    def __init__(
            self,
            pins: tp.Tuple[tp.SupportsIndex, tp.SupportsIndex, tp.SupportsIndex, tp.SupportsIndex],
            step_count: int = 4096,
            step_sleep: float = 0.002,
    ) -> None:
        self._pins = pins
        self._step_count = step_count
        self._step_sleep = step_sleep

        # default values
        self._target_absolute_step = 0
        self._absolute_step = 0
        self._stepper_step = 0

        # threading
        self.pool = ThreadPoolExecutor(max_workers=1)

        self._setup_pins()

    def _setup_pins(self) -> None:
        """
        initializes the stepper pins
        """
        for pin in self._pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)

    def _thread(self) -> None:
        while self.running:
            step_delta = self._target_absolute_step - self._absolute_step

            if step_delta != 0:
                if step_delta > 0:
                    self._absolute_step += 1
                    self._stepper_step = (self._stepper_step + 1) % len(STEP_SEQUENCE)

                else:
                    self._absolute_step -= 1
                    self._stepper_step = (self._stepper_step - 1) % len(STEP_SEQUENCE)

                current_step = STEP_SEQUENCE[self._stepper_step]
                for pin_index, pin in enumerate(self._pins):
                    GPIO.output(pin, current_step[pin_index])

                time.sleep(self._step_sleep)

            else:
                time.sleep(.005)

    def step(self, steps: int) -> None:
        """
        step n amount of steps
        """
        self._target_absolute_step += steps

    def wait_for_step(self) -> None:
        """
        waits until the stepper has reached its target
        """
        while self._target_absolute_step - self._absolute_step != 0:
            time.sleep(.01)

    def cleanup(self) -> None:
        """
        cleans up the steppers pins and threads
        """
        for pin in self._pins:
            GPIO.output(pin, GPIO.LOW)

        self.running = False
        self.pool.shutdown()


if __name__ == "__main__":
    from _pinout import X_MOTOR_PINS
    s = Stepper(X_MOTOR_PINS)
    s.step(200)
    s.wait_for_step()
    s.step(-200)
    s.wait_for_step()
