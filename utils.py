import struct

def create_realtime_payload(data):
    # Initialize an empty list to store the byte sequences
    bytes_list = []

    for entry in data:
        md5_hash = entry['md5']  # 16 bytes
        float_value = entry['value']  # float value to be converted to 4 bytes
        
        # Ensure the MD5 hash is exactly 16 bytes
        if len(md5_hash) != 16:
            raise ValueError("MD5 hash must be exactly 16 bytes")

        # Convert the float to 4 bytes (little-endian format)
        float_bytes = struct.pack('<f', float_value)
        
        # Combine MD5 hash and float bytes, and append to the list
        bytes_list.append(md5_hash + float_bytes)

    # Join all byte sequences into a single bytes object
    return b''.join(bytes_list)


import socket
import platform
import subprocess
import re

def check_internet_connection(host="8.8.8.8", port=53, timeout=3):
    """
    Checks if the system can connect to the internet by reaching a reliable host.
    
    :param host: IP address of the host to connect to (default: 8.8.8.8).
    :param port: Port number to use for the connection (default: 53).
    :param timeout: Timeout in seconds for the connection attempt.
    :return: True if the internet connection is available, False otherwise.
    """
    try:
        with socket.create_connection((host, port), timeout):
            return True
    except (socket.timeout, socket.error):
        return False


import platform


def get_default_gateway():
    """
    Retrieves the default gateway for the active network adapter.
    :return: The default gateway IP address as a string, or None if not found.
    """
    system_platform = platform.system().lower()
    try:
        if "windows" in system_platform:
            # Windows: Use `route print` or `ipconfig`
            output = subprocess.check_output("ipconfig", encoding="utf-8")
            match = re.search(r"Default Gateway[^\n]*:\s+([\d\.]+)", output)
            if match:
                return match.group(1)
        elif "linux" in system_platform or "darwin" in system_platform:
            try:
                with open("/proc/net/route", "r") as f:
                    for line in f.readlines():
                        fields = line.strip().split()
                        if fields[1] == "00000000":  # Default route
                            gateway_hex = fields[2]
                            gateway_ip = ".".join(str(int(gateway_hex[i:i+2], 16)) for i in range(6, -1, -2))
                            return gateway_ip
            except FileNotFoundError as e:
                print(e)
                return None
        else:
            print(f"Platform '{system_platform}' not supported.")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(e)
        return None
    return None

def check_gateway_connection():
    """
    Checks if the system can reach the network gateway dynamically.
    :return: True if the gateway is reachable, False otherwise.
    """
    gateway = get_default_gateway()
    if not gateway:
        print("Default gateway could not be determined.")
        return False
    
    param = "-n" if platform.system().lower() == "windows" else "-c"
    command = ["ping", param, "1", gateway]
    try:
        
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        #print(f"Gateway {gateway} is reachable.")
        return True
    except subprocess.CalledProcessError:
        #print(f"Gateway {gateway} is not reachable.")
        return False

# Example usage:
if __name__ == "__main__":
    print("Checking internet connection...")
    print("Internet is available." if check_internet_connection() else "No internet connection.")

    print("\nChecking gateway connection...")
    print(f"Gateway is: {get_default_gateway()}")
    print("Gateway is reachable" if check_gateway_connection() else "Gateway is not reachable.")

   