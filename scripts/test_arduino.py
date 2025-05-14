#!/usr/bin/env python3
"""
Script to test Arduino connection
"""

import os
import sys
import argparse
import time

# Add main directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.communication.arduino_interface import ArduinoInterface

def parse_arguments():
    parser = argparse.ArgumentParser(description="Arduino Connection Test")
    parser.add_argument("--port", type=str, default="/dev/ttyUSB0", help="Arduino serial port")
    parser.add_argument("--baud", type=int, default=9600, help="Baudrate")
    return parser.parse_args()

def main():
    args = parse_arguments()
    
    print(f"Attempting to connect to Arduino on {args.port} with baudrate {args.baud}")
    
    # Create interface
    arduino = ArduinoInterface(port=args.port, baudrate=args.baud)
    
    # Connect
    if not arduino.connect():
        print("Could not connect to Arduino. Verify it is connected and the port is correct.")
        return 1
    
    print("Connection established!")
    
    # Communication test
    try:
        print("Sending test command...")
        arduino.send_command("TEST")
        
        print("Waiting for response...")
        response = arduino.read_response(timeout=2.0)
        
        if response:
            print(f"Response received: '{response}'")
        else:
            print("No response received.")
        
        # Simple test loop
        print("\nRunning continuous communication test (press Ctrl+C to stop)...")
        count = 0
        while True:
            arduino.send_command(f"PING:{count}")
            response = arduino.read_response()
            if response:
                print(f"Command {count} -> Response: {response}")
            else:
                print(f"Command {count} -> No response")
            count += 1
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
    finally:
        # Disconnect
        arduino.disconnect()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
