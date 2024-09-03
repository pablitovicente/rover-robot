import serial

# Configure the serial connection (adjust settings as needed)
ser = serial.Serial('/dev/serial0', 115200, timeout=1)

try:
    while True:
        if ser.in_waiting > 0:
            data = ser.readline().decode('utf-8').rstrip()
            print(f"Received: {data}")
except KeyboardInterrupt:
    print("Exiting...")
finally:
    ser.close()
