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
    import RPi.GPIO as GPIO
    PIGPIO = True

except ImportError:
    GPIO = ...
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
            speed: float = 500,
    ) -> None:
        self._pins = pins
        self._step_count = step_count
        self._last_speed = speed
        self.speed = speed

        # default values
        self._target_absolute_step = 0
        self._absolute_step = 0
        self._at_speed = 0
        self._move = True

        # threading
        self.pool = ThreadPoolExecutor(max_workers=1)
        self.pool.submit(self._thread)

        self._setup_pins()

    @property
    def target(self) -> int:
        """
        the targeted step
        """
        return self._target_absolute_step

    def current(self) -> int:
        """
        the current step
        """
        return self._absolute_step

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

            if (step_delta != 0 or self._at_speed != 0) and self._move:
                print(f"step delta: ", step_delta)

                # if speed gets too small, skip step (may cause division by zero)
                if self.speed < .01:
                    time.sleep(.005)
                    continue

                match self._at_speed:
                    case 0:
                        if step_delta > 0:
                            self._absolute_step += 1

                        else:
                            self._absolute_step -= 1

                    case -1:
                        self._absolute_step -= 1

                    case 1:
                        self._absolute_step += 1

                    case _:
                        raise ValueError(f"Invalid value for \"at_speed\": {self._at_speed}")

                current_step = STEP_SEQUENCE[self._absolute_step % 8]
                for pin_index, pin in enumerate(self._pins):
                    GPIO.output(pin, current_step[pin_index])

                time.sleep(1 / self.speed)

            else:
                time.sleep(.005)

    def step(self, steps: int) -> None:
        """
        step n amount of steps
        """
        self._target_absolute_step += steps

    def step_from_current(self, steps: int) -> None:
        """
        step n amounts of steps, but starting from the motors current position
        """
        self._target_absolute_step = self._absolute_step + steps

    def move_at_speed(self, speed: float) -> None:
        self._last_speed = self.speed
        self.speed = abs(speed)
        self._at_speed = speed / abs(speed)

        # in case the motor was stopped, resume
        self._move = True

    def stop(self) -> None:
        self.speed = self._last_speed
        self._at_speed = 0
        self._move = False

    def resume(self) -> None:
        self._move = True

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
    s.step(1000)
    s.wait_for_step()

    time.sleep(5)

    s.move_at_speed(-400)
    time.sleep(5)
    s.stop()

    s.cleanup()
