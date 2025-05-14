import serial
import time

class ArduinoInterface:
    """
    Class for Arduino communication.
    Manages sending commands and receiving feedback.
    """
    def __init__(self, port='/dev/ttyUSB0', baudrate=9600, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn = None
        self.connected = False
    
    def connect(self):
        """Establishes connection with Arduino"""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            time.sleep(2)  # Wait for Arduino to initialize
            self.connected = True
            print(f"Connection established with Arduino on {self.port}")
            return True
        except Exception as e:
            print(f"Error connecting to Arduino: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Closes the connection with Arduino"""
        if self.serial_conn and self.connected:
            self.serial_conn.close()
            self.connected = False
            print("Disconnected from Arduino")
    
    def send_command(self, command):
        """Sends a command to Arduino"""
        if not self.connected or not self.serial_conn:
            print("Arduino not connected. Cannot send commands.")
            return False
        
        try:
            # Add line terminator
            if not command.endswith('\n'):
                command += '\n'
            
            # Send command as bytes
            self.serial_conn.write(command.encode())
            return True
        except Exception as e:
            print(f"Error sending command: {e}")
            return False
    
    def read_response(self, timeout=1.0):
        """Reads the response from Arduino"""
        if not self.connected or not self.serial_conn:
            print("Arduino not connected. Cannot read responses.")
            return None
        
        try:
            # Set timeout for reading
            self.serial_conn.timeout = timeout
            
            # Read response
            response = self.serial_conn.readline().decode().strip()
            return response
        except Exception as e:
            print(f"Error reading response: {e}")
            return None
    
    def send_path(self, path):
        """
        Sends a complete path to Arduino.
        The path is a list of (x, y) coordinates.
        """
        if not path:
            print("Empty path. Nothing to send.")
            return False
        
        # Send path length
        self.send_command(f"PATH_LEN:{len(path)}")
        time.sleep(0.1)
        
        # Send each path point
        for i, (x, y) in enumerate(path):
            self.send_command(f"PATH_POINT:{i},{x},{y}")
            response = self.read_response()
            
            # Verify that Arduino received correctly
            if not response or not response.startswith("OK"):
                print(f"Error sending point {i}: {response}")
                return False
            
            time.sleep(0.05)  # Short pause between commands
        
        # Command to start following the path
        self.send_command("PATH_FOLLOW")
        return True
