#!/usr/bin/env python

import time
import sys
import signal
from base_ctrl import BaseController
import VL53L1X

def is_raspberry_pi5():
    """Detect if the current hardware is a Raspberry Pi 5."""
    with open('/proc/cpuinfo', 'r') as file:
        for line in file:
            if 'Model' in line and 'Raspberry Pi 5' in line:
                return True
    return False

def setup_base_controller():
    """Setup and return the base controller based on the Raspberry Pi model."""
    if is_raspberry_pi5():
        print("thinks is a pi5")
        return BaseController('/dev/ttyAMA0', 115200)
    else:
        print("thinks is other")
        return BaseController('/dev/serial0', 115200)

def setup_tof_sensor():
    """Initialize and return the VL53L1X ToF sensor."""
    tof = VL53L1X.VL53L1X(i2c_bus=3, i2c_address=0x29)
    tof.open()
    tof.start_ranging(3)  # Long Range
    return tof

def exit_handler(signal, frame, base, tof):
    """Gracefully handle program exit."""
    global running
    running = False
    tof.stop_ranging()
    base.send_command({"T": 1, "L": 0, "R": 0})  # Stop the motors
    print()
    sys.exit(0)

def get_distance(tof):
    """Get the current distance from the ToF sensor."""
    return tof.get_distance()

def look_around(base, tof):
    """Look left and right, return the direction with the longer path."""
    # Look left
    base.send_command({"T": 1, "L": -0.4, "R": 0.4})  # Turn left
    time.sleep(1)  # Wait for the turn to complete
    left_distance = get_distance(tof)
    print("Left distance: {}mm".format(left_distance))
    
    # Look right
    base.send_command({"T": 1, "L": 0.4, "R": -0.4})  # Turn back to original position
    time.sleep(1)
    base.send_command({"T": 1, "L": 0.4, "R": -0.4})  # Turn right
    time.sleep(1)
    right_distance = get_distance(tof)
    print("Right distance: {}mm".format(right_distance))
    
    # Return to the original position
    base.send_command({"T": 1, "L": -0.4, "R": 0.4})  # Turn back to original position
    time.sleep(1)

    # Determine the longer path and return direction
    if left_distance > right_distance:
        print("Choosing the left path.")
        return "left"
    else:
        print("Choosing the right path.")
        return "right"

def move_forward(base):
    """Send the command to move the robot forward."""
    base.send_command({"T": 1, "L": 0.3, "R": 0.3})

def stop_motors(base):
    """Stop the robot's motors."""
    base.send_command({"T": 1, "L": 0, "R": 0})

def avoid_obstacle(base, tof):
    """Handle obstacle detection and avoidance."""
    direction = look_around(base, tof)
    if direction == "left":
        base.send_command({"T": 1, "L": -0.4, "R": 0.4})  # Turn left
    else:
        base.send_command({"T": 1, "L": 0.4, "R": -0.4})  # Turn right
    time.sleep(2)  # Complete the turn
    move_forward(base)

def main():
    """Main program loop."""
    global running
    running = True

    base = setup_base_controller()
    tof = setup_tof_sensor()

    # Attach signal handler for graceful exit
    signal.signal(signal.SIGINT, lambda sig, frame: exit_handler(sig, frame, base, tof))

    last_command_time = time.time()

    try:
        # Start moving forward immediately
        move_forward(base)

        while running:
            current_time = time.time()

            # Check if it's time to send the next movement command
            if current_time - last_command_time >= 2:
                move_forward(base)
                last_command_time = current_time

            # Get the distance from the sensor
            distance_in_mm = get_distance(tof)
            print("Distance: {}mm".format(distance_in_mm))

            if distance_in_mm <= 400:  # If distance is 30 cm or less
                print("Obstacle detected! Stopping the motors.")
                stop_motors(base)

                # Avoid the obstacle by looking around
                avoid_obstacle(base, tof)

                # Reset the timer after obstacle avoidance
                last_command_time = time.time()

            time.sleep(0.1)  # Shorter sleep for more frequent checks

    except KeyboardInterrupt:
        exit_handler(None, None, base, tof)

if __name__ == '__main__':
    main()
