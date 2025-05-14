#!/usr/bin/env python3
"""
Launch script for the Robot Path Planning Simulation GUI
"""

import os
import sys
import tkinter as tk

# Add parent directory to path to ensure correct imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.visualization.gui.simulation_gui import SimulationGUI

def main():
    """
    Main function to launch the GUI
    """
    root = tk.Tk()
    app = SimulationGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
