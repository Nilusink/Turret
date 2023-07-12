#!/usr/bin/python3
from picamera.array import PiRGBArray
from traceback import print_exc
from picamera import PiCamera
from threading import Thread
import RPi.GPIO as GPIO
import math
import io
import socket
import struct
import time
import picamera


STEPPER_WAIT: float = .5
CAM_RESOLUTION: tuple[int, int] = (1200, 800)
SWIVEL_TIME: float = 15
SWIVEL_RANGE: int = 350
WAIT_FOR_TARGET: float = 5

LASER_PIN: int = 16

in1 = 4
in2 = 17
in3 = 23
in4 = 24

# careful lowering this, at some point you run into the mechanical
# limitation of how quick your motor can move
step_sleep = 0.002

step_count = 4096  # 5.625*(1/64) per step, 4096 steps is 360°

# defining stepper motor sequence (found in documentation
# http://www.4tronix.co.uk/arduino/Stepper-Motors.php)
step_sequence = [[1, 0, 0, 1], [1, 0, 0, 0], [1, 1, 0, 0], [0, 1, 0, 0],
                 [0, 1, 1, 0], [0, 0, 1, 0], [0, 0, 1, 1], [0, 0, 0, 1]]

# setting up
GPIO.setmode(GPIO.BCM)

motor_pins = [in1, in2, in3, in4]
motor2_pins = [21, 20, 26, 19]

for pin in (*motor_pins, *motor2_pins, LASER_PIN):
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)


def cleanup():
    for pin in (motor_pins, motor2_pins):
        GPIO.output(pin, GPIO.LOW)

    GPIO.output(LASER_PIN, GPIO.LOW)
    GPIO.cleanup()


# offset y, thread running, offset x, target found
direction = [0, True, 0, False]


def stepper_thread():
    global motor_pins, direction
    motor_step_counter = 0
    motor2_step_counter = 0

    last_seen = 0
    while direction[1]:
        sin_val = math.sin(((time.perf_counter() * math.pi * 2) / SWIVEL_TIME))
        
        if direction[3]:
            GPIO.output(LASER_PIN, GPIO.HIGH)
            last_seen = time.perf_counter()
            off_y = direction[0]
            direction[0] = 0

            off_x = direction[2]
            direction[2] = 0

            if off_y or off_x:
                direc_y = off_y < 0
                steps_y = int(abs(off_y))

                direc_x = off_x < 0
                steps_x = int(abs(off_x))

                for _ in range(max(steps_y, steps_x)):
                    # y
                    steps_y -= 1
                    if steps_y > 0:
                        for pin in range(0, len(motor_pins)):
                            GPIO.output(
                                motor_pins[pin], step_sequence[motor_step_counter % 8][pin]
                                )

                        if direc_y:
                            motor_step_counter -= 1

                        else:
                            motor_step_counter += 1

                    steps_x -= 1
                    if steps_x > 0:
                        for pin in range(0, len(motor2_pins)):
                            GPIO.output(
                                motor2_pins[pin],
                                step_sequence[motor2_step_counter % 8][pin]
                            )

                        if direc_x:
                            motor2_step_counter -= 1

                        else:
                            motor2_step_counter += 1

                    time.sleep(step_sleep)

                # after moving, wait for camera to reload
                time.sleep(STEPPER_WAIT)

        # target not found
        elif time.perf_counter() - last_seen > WAIT_FOR_TARGET:
            GPIO.output(LASER_PIN, GPIO.LOW)

            if motor_step_counter > 0:
                motor_step_counter -= 1

            elif motor_step_counter < 0:
                motor_step_counter += 1

            x_should = sin_val * SWIVEL_RANGE

            # print(f"\r{motor_step_counter=}", end="", flush=True)
            # print(f"\r{x_should=}, {motor2_step_counter=}", end="", flush=True)

            if motor2_step_counter > x_should:
                motor2_step_counter -= 1

            elif motor2_step_counter < x_should:
                motor2_step_counter += 1

            for pin in range(0, len(motor_pins)):
                GPIO.output(
                    motor_pins[pin],
                    step_sequence[motor_step_counter % 8][pin]
                )

            for pin in range(0, len(motor2_pins)):
                GPIO.output(
                    motor2_pins[pin],
                    step_sequence[motor2_step_counter % 8][pin]
                )

            time.sleep(step_sleep)

    print("stepper exit")


# Connect a client socket to my laptop's IP address and port 8000
client_socket = socket.socket()
client_socket.connect(('10.42.0.1', 8000))

# Make a file-like object out of the connection
connection = client_socket.makefile('rwb')

try:
    Thread(target=stepper_thread).start()

    with picamera.PiCamera() as camera:
        camera.resolution = CAM_RESOLUTION
        camera.framerate = 32
        time.sleep(2)  # Let camera warm up
        stream = io.BytesIO()

        for _ in camera.capture_continuous(
                stream, 'jpeg', use_video_port=True
                ):
            start = time.perf_counter()
            # Send the image length and data over the network
            connection.write(struct.pack('<L', stream.tell()))
            connection.flush()
            stream.seek(0)
            connection.write(stream.read())
            stream.seek(0)
            stream.truncate()

            # # Receive an integer from the laptop
            target_found = struct.unpack('<i', connection.read(struct.calcsize(
                '<i')))[0]

            off_y = struct.unpack('<i', connection.read(struct.calcsize(
                '<i')))[0]
            off_x = struct.unpack('<i', connection.read(struct.calcsize(
                '<i')))[0]
            direction[0] = int(off_y)
            direction[2] = int(off_x)
            direction[3] = bool(target_found)

            took = (time.perf_counter() - start) * 1000
            print(f"\rtook {took:.2f}ms", end="", flush=True)

finally:
    connection.close()
    client_socket.close()

    direction[1] = False
    time.sleep(5)

    cleanup()
    exit(1)
