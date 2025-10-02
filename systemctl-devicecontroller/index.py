import threading
import socket
import time
from rpi_ws281x import PixelStrip, Color
from mobil_com import MobilCom
from dotenv import load_dotenv
from pathlib import Path
import os
import sys

# Configuration for the WS2812B-2020 LED
LED_COUNT = 1         # Only one LED
LED_PIN = 12          # GPIO pin (PWM)
LED_FREQ_HZ = 800000  # LED signal frequency
LED_DMA = 10          # DMA channel
LED_BRIGHTNESS = 255  # Brightness (0-255)
LED_INVERT = False    # Signal inversion
LED_CHANNEL = 0       # Channel

CONFIG_PATH = '/etc/devicecontroller/config.env'

# Load the .env file
env_path = Path(CONFIG_PATH)
load_dotenv(dotenv_path=env_path)

apn = os.getenv('APN')
mc = MobilCom(apn)

# Initialize LED
strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()
debug = ('-d' in sys.argv or '-debug' in sys.argv)

def set_color(strip, color):
    """Set the LED to a specific color."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
    strip.show()


def update_env_value(file_path, key, new_value):
    """Update the value of a key in a .env file."""
    env_path = Path(file_path)

    if not env_path.exists():
        raise FileNotFoundError(f"The .env file at {file_path} does not exist.")

    updated_lines = []
    key_found = False

    # Read the .env file
    with env_path.open('r') as file:
        for line in file:
            if line.startswith(f"{key}="):
                updated_lines.append(f"{key}={new_value}\n")
                key_found = True
            else:
                updated_lines.append(line)

    if not key_found:
        updated_lines.append(f"{key}={new_value}\n")

    with env_path.open('w') as file:
        file.writelines(updated_lines)

    if debug: print(f"Updated {key} in {file_path} to: {new_value}")


def socket_server():
    """Blocking socket server for communication."""
    host = "127.0.0.1"
    port = 65432

    # Create and configure the server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(5)

    server_socket.settimeout(None)  # Explicitly disable timeout
    if debug: print(f"Blocking socket server listening on {host}:{port}...")

    try:
        while True:
            client_socket = None  # Initialize to None at the start of each loop
            # Accept a new client connection (blocking)
            try:
                client_socket, addr = server_socket.accept()
                if debug: print(f"New connection from {addr}")

                # Handle client communication in a blocking loop
                while True:
                    data = client_socket.recv(1024).decode().strip()
                    if not data:
                        if debug: print(f"Connection closed by {addr}")
                        break

                    if debug: print(f"Received from {addr}: {data}")

                    # Process commands
                    if 'set-color' in data:
                        try:
                            _, r, g, b = data.split(' ')
                            set_color(strip, Color(int(r), int(g), int(b)))
                            response = "OK\n"
                        except (ValueError, IndexError):
                            response = "ERROR: Invalid color format\n"
                    elif 'set-apn' in data:
                        try:
                            _, new_apn = data.split(' ')
                            mc.set_apn(new_apn)
                            update_env_value(CONFIG_PATH, 'APN', new_apn)
                            response = "OK\n"
                        except Exception as e:
                            response = f"ERROR: Unable to set APN: {e}\n"
                    elif 'get-apn' in data:
                        response = f"OK {mc.apn}\n"
                    elif 'AT+CSQ' in data:
                        try:
                            rssi, ber = mc.AT_CSQ()
                            response = f"AT+CSQ: {rssi}, {ber}\n"
                        except Exception:
                            response = "ERROR: Failed to retrieve signal quality\n"
                    elif 'AT+STATUS' in data:
                        response = f"State: {mc.state}\n"
                    else:
                        response = "ERROR: Unknown command\n"

                    # Send response to the client
                    client_socket.sendall(response.encode())
            except socket.timeout:
                if debug: print("Socket timed out. Retrying...")
                continue
            except ConnectionResetError:
                if debug: print(f"Connection reset by client.")
            finally:
                if client_socket: client_socket.close()
    finally:
        server_socket.close()


def mc_loop_thread():
    """Thread to handle MobilCom updates and periodic tasks."""
    last_round = time.time()

    while True:
        tp = time.time() - last_round
        last_round = time.time()
        mc.loop(tp * 1000)  # Pass milliseconds
        time.sleep(0.01)


def main():
    # Create threads for the socket server and MobilCom loop
    mobilcom_thread = threading.Thread(target=mc_loop_thread, daemon=True)

    # Start the threads
    mobilcom_thread.start()

    socket_server()


if __name__ == '__main__':
    main()
