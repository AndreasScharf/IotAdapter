import socket


class DeviceControllerClient(object):
    """
    A client class to communicate with the Device Controller server.
    """
    def __init__(self, host="127.0.0.1", port=65432):
        """
        Initialize the client with the server's host and port.
        """
        self.host = host
        self.port = port
        self.socket = None


        self.connected = False
        self._status_color = ( 0, 0, 0 )

        self.block_client = 5

    def connect(self):
        return 

        if self.block_client == 0:
            return

        """
        Connect to the server.
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))

            self.connected = True
            self.block_client = 5

        except Exception as e:
            self.socket = None
            self.block_client = self.block_client - 1
            print(f"Failed Connected to server at {self.host}:{self.port}")


    def send_command(self, command):
        """
        Send a command to the server and return the response.
        """
        if not self.socket:
            self.connect()
        
        if not self.connected:
            return ""

        try:
            self.socket.sendall(command.encode())
            response = self.socket.recv(1024).decode().strip()

            if self.socket:
                self.socket.close()
                self.socket = None

            return response
        except Exception as e:
            try:
                if self.socket:
                    self.socket.close()
                    self.socket = None
            except:
                pass

            return f"ERROR: {e}"

    def disconnect(self):
        """
        Disconnect from the server.
        """
        if self.socket:
            self.socket.close()
            self.socket = None
            print("Disconnected from server.")

    def _update_LED(self):

        r, g, b = self._status_color

        command = f"set-color {r} {g} {b}"
        return self.send_command(command)
    
    # Specific command methods for convenience
    def set_color(self, r, g, b):
        """
        Send a command to set the LED color.
        """
        self._status_color = r, g, b



    def set_apn(self, apn):
        """
        Send a command to set the APN.
        """
        command = f"set-apn {apn}"
        return self.send_command(command)
    
    def get_apn(self):
        """
        Send a command to retrieve the APN.
        """
        command = "get-apn"
        response = self.send_command(command)
        print(response)
        return self._decode_get_apn(response)

    def get_signal_quality(self):
        """
        Send a command to retrieve the signal quality and decode the response.
        """
        command = "AT+CSQ"
        response = self.send_command(command)
        return self._decode_signal_quality(response)

    def get_status(self):
        """
        Send a command to retrieve the current status and decode the response.
        """
        command = "AT+STATUS"
        response = self.send_command(command)
        return self._decode_status(response)

    # Decoding mechanisms
    def _decode_signal_quality(self, response):
        """
        Decode the AT+CSQ response into a human-readable format.
        Response format: "AT+CSQ: <rssi>, <ber>"
        """
        try:
            if response.startswith("AT+CSQ:"):
                parts = response.split(":")[1].strip().split(",")
                rssi = int(float(parts[0]))
                ber = int(float(parts[1]))
                return (rssi, ber)
            else:
                raise ValueError("Invalid response format")
        except Exception as e:
            print(e)
            return {"error": "Failed to decode AT+CSQ response", "raw_response": response}

    def _decode_status(self, response):
        """
        Decode the AT+STATUS response into a human-readable format.
        Response format: "State: <state>"
        """
        try:
            if response.startswith("State:"):
                parts = response.split(":")[1].strip().split(",")
                state = int(parts[0])
                connection = int(parts[1])
                return (state, connection)
            else:
                raise ValueError("Invalid response format")
        except Exception:
            return {"error": "Failed to decode AT+STATUS response", "raw_response": response}
        
    def _decode_get_apn(self, response):
        """
        Decode the get-apn response into a human-readable format.
        Response format: "OK <state>"
        """
        try:
            if response.startswith("OK"):
                state = response.split(" ")[1].strip()
                return state
            else:
                raise ValueError("Invalid response format")
        except Exception as e:
            print(e)
            return {"error": "Failed to decode get-apn response", "raw_response": response}

   

    

