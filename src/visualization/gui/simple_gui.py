import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import time
import threading

from src.environment.enhanced_environment import EnhancedEnvironment
from src.environment.models.terrain import TerrainType
from src.planning.path_planner import PathPlanner
from src.robot.kinematics.differential_drive import DifferentialDriveModel
from src.robot.kinematics.path_follower import PathFollower

class SimpleSimulationGUI:
    """
    Simplified GUI for the robot path planning simulation
    with click-to-set-target functionality
    """
    def __init__(self, root):
        self.root = root
        self.root.title("Robot Path Planning Simulation")
        self.root.geometry("1000x700")
        
        # Create the environment and planner
        self.env = EnhancedEnvironment(50, 50)  # Default size
        self.planner = PathPlanner(self.env)
        
        # Robot models
        self.drive_model = DifferentialDriveModel()
        self.path_follower = PathFollower(self.drive_model)
        
        # Simulation variables
        self.robot_pose = (2, 2, 0)  # x, y, theta
        self.path = None
        self.running = False
        self.simulation_thread = None
        self.sim_speed = 1.0  # Simulation speed multiplier
        
        # Create the UI
        self.create_widgets()
        
    def create_widgets(self):
        """
        Create all the widgets for the GUI
        """
        # Main layout
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top panel with controls - simplified to just a few essential buttons
        self.control_frame = ttk.Frame(self.main_frame, padding="5")
        self.control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Generate terrain button
        self.generate_button = ttk.Button(self.control_frame, text="Generate New Environment", command=self.generate_environment)
        self.generate_button.pack(side=tk.LEFT, padx=5)
        
        # Plan path button
        self.plan_button = ttk.Button(self.control_frame, text="Plan Path", command=self.plan_path)
        self.plan_button.pack(side=tk.LEFT, padx=5)
        
        # Start/stop simulation button
        self.simulate_button = ttk.Button(self.control_frame, text="Start Simulation", command=self.toggle_simulation)
        self.simulate_button.pack(side=tk.LEFT, padx=5)
        
        # Reset button
        self.reset_button = ttk.Button(self.control_frame, text="Reset", command=self.reset_simulation)
        self.reset_button.pack(side=tk.LEFT, padx=5)
        
        # Instruction label
        self.instruction_label = ttk.Label(self.control_frame, text="Click anywhere on the map to set the target position")
        self.instruction_label.pack(side=tk.RIGHT, padx=5)
        
        # Main visualization area
        self.canvas_frame = ttk.Frame(self.main_frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create matplotlib figure
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.canvas_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add mouse click event to the canvas
        self.canvas.mpl_connect('button_press_event', self.on_click)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready - Click anywhere to set target position")
        self.status_bar = ttk.Label(self.main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, padx=5, pady=2)
        
        # Generate initial environment
        self.generate_environment()
        
    def generate_environment(self):
        """
        Generate a new environment with obstacles
        """
        # Create new environment (50x50 grid)
        self.env = EnhancedEnvironment(50, 50)
        
        # Add some random obstacles (simplified terrain)
        # Start with all free cells
        self.env.grid = np.zeros((self.env.height, self.env.width), dtype=int)
        
        # Add random obstacle clusters
        for _ in range(30):  # Add 30 obstacle clusters
            x = np.random.randint(5, self.env.width-5)  # Keep borders free
            y = np.random.randint(5, self.env.height-5)
            size = np.random.randint(1, 4)  # Random size between 1 and 3
            self.env.add_terrain(x, y, size, size, TerrainType.OBSTACLE)
        
        # Update planner
        self.planner = PathPlanner(self.env)
        
        # Reset simulation
        self.reset_simulation()
        
        # Set robot position in bottom-left corner
        self.env.set_robot_pos(2, 2)
        self.robot_pose = (2, 2, 0)  # x, y, theta
        
        # Default goal position in top-right corner
        self.env.set_goal_pos(45, 45)
        
        # Update display
        self.update_display()
        self.status_var.set("New environment generated. Click anywhere to set target position.")
        
    def on_click(self, event):
        """
        Handle mouse click event to set target position
        """
        # Only handle clicks within the plot area
        if event.xdata is None or event.ydata is None:
            return
            
        # Convert to grid coordinates
        x = int(event.xdata)
        y = int(event.ydata)
        
        # Check if position is valid
        if 0 <= x < self.env.width and 0 <= y < self.env.height:
            if not self.env.is_valid_position(x, y):
                self.status_var.set("Cannot set target in obstacle. Please choose another location.")
                return
                
            # Set new goal position
            self.env.set_goal_pos(x, y)
            self.status_var.set(f"Target set to ({x}, {y}). Press 'Plan Path' to calculate route.")
            
            # Update display
            self.update_display()
            
            # Clear previous path
            self.path = None
        
    def plan_path(self):
        """
        Plan a path using A* algorithm
        """
        if self.env.robot_pos is None or self.env.goal_pos is None:
            self.status_var.set("Set robot and goal positions first!")
            return
            
        self.status_var.set("Planning path...")
        self.root.update()
        
        # Plan the path with A*
        self.path = self.planner.a_star()
        
        if self.path:
            self.path_follower.set_path(self.path)
            self.status_var.set(f"Path planned successfully with {len(self.path)} points")
        else:
            messagebox.showerror("Planning Failed", "Could not find a valid path!")
            self.status_var.set("Path planning failed")
            
        # Update display
        self.update_display()
        
    def toggle_simulation(self):
        """
        Start or stop the simulation
        """
        if not self.path:
            messagebox.showwarning("No Path", "Please plan a path first!")
            return
            
        if self.running:
            # Stop simulation
            self.running = False
            self.simulate_button.config(text="Start Simulation")
            self.status_var.set("Simulation stopped")
        else:
            # Start simulation
            self.running = True
            self.simulate_button.config(text="Stop Simulation")
            self.status_var.set("Simulation running")
            
            # Start simulation in a separate thread
            if self.simulation_thread is None or not self.simulation_thread.is_alive():
                self.simulation_thread = threading.Thread(target=self.run_simulation)
                self.simulation_thread.daemon = True
                self.simulation_thread.start()
                
    def reset_simulation(self):
        """
        Reset the simulation to initial state
        """
        # Stop simulation if running
        self.running = False
        
        # Reset robot position to bottom-left
        self.robot_pose = (2, 2, 0)
        self.env.set_robot_pos(2, 2)
        
        # Clear path
        self.path = None
        
        # Update display
        self.update_display()
        self.status_var.set("Simulation reset - Click anywhere to set target position")
        self.simulate_button.config(text="Start Simulation")
        
    def run_simulation(self):
        """
        Run the simulation loop
        """
        # Reset to start position
        self.robot_pose = (self.env.robot_pos[0], self.env.robot_pos[1], 0)
        
        dt = 0.1  # Time step
        last_time = time.time()
        
        while self.running:
            # Calculate actual time step
            current_time = time.time()
            actual_dt = (current_time - last_time) * self.sim_speed
            last_time = current_time
            
            # Update robot pose
            left_vel, right_vel, reached_goal = self.path_follower.update(self.robot_pose, dt)
            
            # If goal reached, stop
            if reached_goal:
                self.status_var.set("Goal reached!")
                self.running = False
                self.simulate_button.config(text="Start Simulation")
                break
                
            # Update robot pose based on wheel velocities
            self.robot_pose = self.drive_model.update_pose(self.robot_pose, left_vel, right_vel, actual_dt)
            
            # Update display
            self.update_display()
            
            # Sleep to maintain reasonable frame rate
            time.sleep(0.05)
            
    def update_display(self):
        """
        Update the display with current environment and robot state
        """
        self.ax.clear()
        
        # Set axis limits
        self.ax.set_xlim(0, self.env.width)
        self.ax.set_ylim(0, self.env.height)
        
        # Draw the obstacles
        for y in range(self.env.height):
            for x in range(self.env.width):
                terrain_type = self.env.grid[y, x]
                if terrain_type == TerrainType.OBSTACLE:
                    self.ax.add_patch(plt.Rectangle((x, y), 1, 1, color='black', alpha=0.7))
        
        # Draw the path if available
        if self.path:
            path_x = [p[0] + 0.5 for p in self.path]
            path_y = [p[1] + 0.5 for p in self.path]
            self.ax.plot(path_x, path_y, 'b-', linewidth=2, alpha=0.7)
        
        # Draw robot
        x, y, theta = self.robot_pose
        robot_radius = 0.4
        
        # Draw robot as a circle with a line indicating orientation
        self.ax.add_patch(plt.Circle((x + 0.5, y + 0.5), robot_radius, color='red', alpha=0.7))
        endx = (x + 0.5) + robot_radius * np.cos(theta)
        endy = (y + 0.5) + robot_radius * np.sin(theta)
        self.ax.plot([x + 0.5, endx], [y + 0.5, endy], 'k-', linewidth=2)
        
        # Draw goal
        if self.env.goal_pos:
            goal_x, goal_y = self.env.goal_pos
            self.ax.add_patch(plt.Circle((goal_x + 0.5, goal_y + 0.5), 0.4, color='green', alpha=0.7))
        
        # Set grid and labels
        self.ax.grid(True, linestyle='--', alpha=0.6)
        self.ax.set_title("Robot Path Planning Simulation - Click to Set Target")
        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Y")
        
        # Update the canvas
        self.canvas.draw()
