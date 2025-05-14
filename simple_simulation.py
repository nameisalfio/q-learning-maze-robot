#!/usr/bin/env python3
"""
Simplified Robot Path Planning Simulation with Click-to-Set-Target

This script runs a simplified version of the path planning simulation
where the user can click on the map to set the target position.
"""

import os
import sys
import tkinter as tk

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Create __init__.py files if they don't exist
os.makedirs("src/robot/sensors", exist_ok=True)
os.makedirs("src/robot/kinematics", exist_ok=True)
os.makedirs("src/environment/models", exist_ok=True)
os.makedirs("src/planning/algorithms", exist_ok=True)
os.makedirs("src/visualization/gui", exist_ok=True)

# Create empty __init__.py files if they don't exist
for path in [
    "src/robot/sensors/__init__.py",
    "src/robot/kinematics/__init__.py",
    "src/environment/models/__init__.py",
    "src/planning/algorithms/__init__.py",
    "src/visualization/gui/__init__.py"
]:
    if not os.path.exists(path):
        with open(path, 'w') as f:
            pass

# Import the simplified GUI
from src.visualization.gui.simple_gui import SimpleSimulationGUI

def main():
    """
    Main function
    """
    root = tk.Tk()
    app = SimpleSimulationGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
