#!/usr/bin/env python

import time
import sys
import signal
from base_ctrl import BaseController
import VL53L1X

# Function for Detecting Raspberry Pi
def is_raspberry_pi5():
    with open('/proc/cpuinfo', 'r') as file:
        for line in file:
            if 'Model' in line:
                if 'Raspberry Pi 5' in line:
                    return True
                else:
                    return False

# Determine the GPIO Serial Device Name Based on the Raspberry Pi Model
if is_raspberry_pi5():
    print("thinks is a pi5")
    base = BaseController('/dev/ttyAMA0', 115200)
else:
    print("thinks is other")
    base = BaseController('/dev/serial0', 115200)

# Initialize the VL53L1X ToF sensor
tof = VL53L1X.VL53L1X(i2c_bus=3, i2c_address=0x29)
tof.open()
tof.start_ranging(3)  # Long Range

running = True

def exit_handler(signal, frame):
    global running
    running = False
    tof.stop_ranging()
    base.send_command({"T": 1, "L": 0, "R": 0})  # Stop the motors
    print()
    sys.exit(0)

# Attach a signal handler to catch SIGINT (Ctrl+C) and exit gracefully
signal.signal(signal.SIGINT, exit_handler)

def get_distance():
    """Helper function to get the current distance from the sensor."""
    return tof.get_distance()

def look_around():
    """Function to look left and right, and return the direction with the longer path."""
    # Look left
    base.send_command({"T": 1, "L": -0.3, "R": 0.3})  # Turn left
    time.sleep(1)  # Wait for the turn to complete
    left_distance = get_distance()
    print("Left distance: {}mm".format(left_distance))
    
    # Look right
    base.send_command({"T": 1, "L": 0.3, "R": -0.3})  # Turn back to the original position
    time.sleep(1)
    base.send_command({"T": 1, "L": 0.3, "R": -0.3})  # Turn right
    time.sleep(1)
    right_distance = get_distance()
    print("Right distance: {}mm".format(right_distance))
    
    # Return to the original position
    base.send_command({"T": 1, "L": -0.3, "R": 0.3})  # Turn back to the original position
    time.sleep(1)

    # Determine the longer path and return direction
    if left_distance > right_distance:
        print("Choosing the left path.")
        return "left"
    else:
        print("Choosing the right path.")
        return "right"

try:
    last_command_time = time.time()

    # Start moving forward immediately
    base.send_command({"T": 1, "L": 0.3, "R": 0.3})

    while running:
        # Get the current time
        current_time = time.time()

        # Check if it's time to send the next movement command
        if current_time - last_command_time >= 2:
            # Continue moving forward
            base.send_command({"T": 1, "L": 0.3, "R": 0.3})
            last_command_time = current_time

        # Get the distance from the sensor
        distance_in_mm = get_distance()
        print("Distance: {}mm".format(distance_in_mm))

        if distance_in_mm <= 400:  # If distance is 30 cm or less
            print("Obstacle detected! Stopping the motors.")
            base.send_command({"T": 1, "L": 0, "R": 0})  # Stop the motors

            # Look left and right to determine the best path
            direction = look_around()

            # Move in the chosen direction
            if direction == "left":
                base.send_command({"T": 1, "L": -0.3, "R": 0.3})  # Turn left
                time.sleep(1)  # Complete the turn
            else:
                base.send_command({"T": 1, "L": 0.3, "R": -0.3})  # Turn right
                time.sleep(1)  # Complete the turn

            # Continue moving forward
            base.send_command({"T": 1, "L": 0.3, "R": 0.3})
            last_command_time = time.time()  # Reset the timer after obstacle avoidance

        time.sleep(0.1)  # Shorter sleep for more frequent checks

except KeyboardInterrupt:
    exit_handler(None, None)
