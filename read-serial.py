import serial

# Open the serial port
ser = serial.Serial('/dev/ttyAMA0', 115200, timeout=1)

# Read data
try:
    while True:
        if ser.in_waiting > 0:
            data = ser.readline().decode('utf-8').rstrip()
            print(data)
except KeyboardInterrupt:
    pass
finally:
    ser.close()
