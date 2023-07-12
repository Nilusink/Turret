import pygame as pg

pg.init()
pg.joystick.init()

surf = pg.display.set_mode((1280, 720), flags=pg.RESIZABLE)

throttle = None

for i in range(pg.joystick.get_count()):
    joystick = pg.joystick.Joystick(i)
    joystick.init()

    if "Throttle" in joystick.get_name():
        print(f"Selected: {joystick.get_name()}")
        throttle = joystick

if throttle is None:
    exit(0)


while True:
    for event in pg.event.get():
        if event.type == pg.JOYDEVICEADDED:
            print(event)

        if event.type == pg.QUIT:
            done = True

    pg.event.pump()
    surf.fill((0, 0, 0, 0))
    

    num_axes = throttle.get_numaxes()
    num_buttons = throttle.get_numbuttons()

    # Read joystick events
    print(f"{throttle.get_name()}: ", end="")
    for i in range(num_axes):
        axis = throttle.get_axis(i)
        print(f"{axis}, ", end="")
        # Process joystick axis input

    for i in range(num_buttons):
        button = throttle.get_button(i)
        print(button, end="")
        # Process joystick button input
    print()

    pg.display.flip()
