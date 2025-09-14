import serial
import time
import sys
import termios
import tty

# === CONFIG ===
SERIAL_PORT = '/dev/ttyUSB0'  # Change this if your Roomba is on a different port
BAUDRATE = 115200
COMMAND_DELAY = 0.15  # Seconds between commands for reliable execution

# === INITIALIZE SERIAL CONNECTION ===
try:
    ser = serial.Serial(SERIAL_PORT, baudrate=BAUDRATE, timeout=1)
except serial.SerialException as e:
    print(f"Cannot open serial port {SERIAL_PORT}: {e}")
    sys.exit(1)

time.sleep(2)  # Give Roomba time to wake up

# === START OI AND SAFE MODE ===
try:
    ser.write(bytes([128]))  # Start OI
    time.sleep(0.1)
    ser.write(bytes([131]))  # Safe Mode
    time.sleep(0.1)
except serial.SerialException as e:
    print(f"Serial error during initialization: {e}")
    ser.close()
    sys.exit(1)

print("Connected to Roomba. Control keys:")
print("W = Forward | S = Backward | A = Turn Left | D = Turn Right")
print("Space = Stop | C = Clean | H = Dock | ESC = Emergency Stop | Q = Quit")

# === HELPER FUNCTIONS ===
def get_key():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def to_bytes(val):
    """Convert signed 16-bit integer to two bytes (big endian)"""
    if val < 0:
        val = 65536 + val  # two's complement
    return (val >> 8) & 0xFF, val & 0xFF

def drive(velocity, radius):
    """Send drive command to Roomba"""
    velocity = max(-500, min(500, velocity))
    radius = max(-2000, min(2000, radius))
    v_high, v_low = to_bytes(velocity)
    r_high, r_low = to_bytes(radius)

    try:
        ser.write(bytes([137, v_high, v_low, r_high, r_low]))
    except serial.SerialException as e:
        print(f"Serial write error: {e}")

    time.sleep(COMMAND_DELAY)

def stop():
    """Stop Roomba"""
    drive(0, 0)

# === MAIN LOOP ===
try:
    while True:
        key = get_key()
        if key == '\x1b':  # ESC key for emergency stop
            stop()
            print("EMERGENCY STOP!")
        else:
            key = key.lower()
            if key == "w":
                drive(200, 0x8000)  # Forward straight
                print("Forward")
            elif key == "s":
                drive(-200, 0x8000)  # Backward straight
                print("Backward")
            elif key == "a":
                stop()
                drive(100, 1)  # Pivot left
                print("Turn Left")
            elif key == "d":
                stop()
                drive(100, -1)  # Pivot right
                print("Turn Right")
            elif key == " ":
                stop()
                print("Stop")
            elif key == "c":
                try:
                    ser.write(bytes([135]))  # Clean
                    print("Clean mode")
                except serial.SerialException as e:
                    print(f"Serial error: {e}")
            elif key == "h":
                try:
                    ser.write(bytes([143]))  # Dock
                    print("Docking")
                except serial.SerialException as e:
                    print(f"Serial error: {e}")
            elif key == "q":
                stop()
                print("Exiting...")
                break

except KeyboardInterrupt:
    stop()
    print("\nInterrupted. Roomba stopped.")

finally:
    stop()
    ser.close()
