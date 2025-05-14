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
from src.planning.multi_planner import MultiPlanner
from src.robot.kinematics.differential_drive import DifferentialDriveModel
from src.robot.kinematics.path_follower import PathFollower
from src.robot.sensors.lidar_sensor import LidarSensor

class SimulationGUI:
    """
    GUI for the robot path planning simulation
    """
    def __init__(self, root):
        self.root = root
        self.root.title("Robot Path Planning Simulation")
        self.root.geometry("1200x800")
        
        # Create the environment and planner
        self.env = EnhancedEnvironment(50, 50)  # Default size
        self.planner = MultiPlanner(self.env)
        
        # Robot models
        self.drive_model = DifferentialDriveModel()
        self.path_follower = PathFollower(self.drive_model)
        
        # Sensors
        self.lidar = LidarSensor(self.env)
        
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
        
        # Top panel with controls
        self.control_frame = ttk.LabelFrame(self.main_frame, text="Controls", padding="10")
        self.control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Environment settings
        self.env_frame = ttk.LabelFrame(self.control_frame, text="Environment")
        self.env_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.Y)
        
        ttk.Label(self.env_frame, text="Width:").grid(row=0, column=0, sticky=tk.W)
        self.width_var = tk.IntVar(value=50)
        ttk.Spinbox(self.env_frame, from_=10, to=100, textvariable=self.width_var, width=5).grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(self.env_frame, text="Height:").grid(row=1, column=0, sticky=tk.W)
        self.height_var = tk.IntVar(value=50)
        ttk.Spinbox(self.env_frame, from_=10, to=100, textvariable=self.height_var, width=5).grid(row=1, column=1, sticky=tk.W)
        
        ttk.Label(self.env_frame, text="Terrain:").grid(row=2, column=0, sticky=tk.W)
        self.terrain_var = tk.DoubleVar(value=0.15)
        ttk.Spinbox(self.env_frame, from_=0.0, to=0.5, increment=0.05, textvariable=self.terrain_var, width=5).grid(row=2, column=1, sticky=tk.W)
        
        ttk.Button(self.env_frame, text="Generate", command=self.generate_environment).grid(row=3, column=0, columnspan=2, pady=5)
        
        # Robot settings
        self.robot_frame = ttk.LabelFrame(self.control_frame, text="Robot")
        self.robot_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.Y)
        
        ttk.Label(self.robot_frame, text="Start X:").grid(row=0, column=0, sticky=tk.W)
        self.start_x_var = tk.IntVar(value=2)
        ttk.Spinbox(self.robot_frame, from_=0, to=100, textvariable=self.start_x_var, width=5).grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(self.robot_frame, text="Start Y:").grid(row=1, column=0, sticky=tk.W)
        self.start_y_var = tk.IntVar(value=2)
        ttk.Spinbox(self.robot_frame, from_=0, to=100, textvariable=self.start_y_var, width=5).grid(row=1, column=1, sticky=tk.W)
        
        ttk.Label(self.robot_frame, text="Goal X:").grid(row=2, column=0, sticky=tk.W)
        self.goal_x_var = tk.IntVar(value=45)
        ttk.Spinbox(self.robot_frame, from_=0, to=100, textvariable=self.goal_x_var, width=5).grid(row=2, column=1, sticky=tk.W)
        
        ttk.Label(self.robot_frame, text="Goal Y:").grid(row=3, column=0, sticky=tk.W)
        self.goal_y_var = tk.IntVar(value=45)
        ttk.Spinbox(self.robot_frame, from_=0, to=100, textvariable=self.goal_y_var, width=5).grid(row=3, column=1, sticky=tk.W)
        
        # Planning settings
        self.planning_frame = ttk.LabelFrame(self.control_frame, text="Planning")
        self.planning_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.Y)
        
        ttk.Label(self.planning_frame, text="Algorithm:").grid(row=0, column=0, sticky=tk.W)
        self.algorithm_var = tk.StringVar(value="a_star")
        ttk.Combobox(self.planning_frame, textvariable=self.algorithm_var, values=["a_star", "rrt", "rrt_star"], width=10).grid(row=0, column=1, sticky=tk.W)
        
        self.optimize_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.planning_frame, text="Optimize Path", variable=self.optimize_var).grid(row=1, column=0, columnspan=2, sticky=tk.W)
        
        self.show_lidar_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.planning_frame, text="Show LIDAR", variable=self.show_lidar_var).grid(row=2, column=0, columnspan=2, sticky=tk.W)
        
        # Simulation controls
        self.sim_frame = ttk.LabelFrame(self.control_frame, text="Simulation")
        self.sim_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.Y)
        
        ttk.Label(self.sim_frame, text="Speed:").grid(row=0, column=0, sticky=tk.W)
        self.speed_var = tk.DoubleVar(value=1.0)
        ttk.Spinbox(self.sim_frame, from_=0.1, to=10.0, increment=0.1, textvariable=self.speed_var, width=5).grid(row=0, column=1, sticky=tk.W)
        
        self.plan_button = ttk.Button(self.sim_frame, text="Plan Path", command=self.plan_path)
        self.plan_button.grid(row=1, column=0, columnspan=2, pady=5)
        
        self.simulate_button = ttk.Button(self.sim_frame, text="Start Simulation", command=self.toggle_simulation)
        self.simulate_button.grid(row=2, column=0, columnspan=2, pady=5)
        
        self.reset_button = ttk.Button(self.sim_frame, text="Reset", command=self.reset_simulation)
        self.reset_button.grid(row=3, column=0, columnspan=2, pady=5)
        
        # Main visualization area
        self.canvas_frame = ttk.Frame(self.main_frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create matplotlib figure
        self.fig = Figure(figsize=(8, 8), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.canvas_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(self.main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, padx=5, pady=2)
        
        # Generate initial environment
        self.generate_environment()
        
    def generate_environment(self):
        """
        Generate a new environment with the specified settings
        """
        width = self.width_var.get()
        height = self.height_var.get()
        terrain_ratio = self.terrain_var.get()
        
        # Create new environment
        self.env = EnhancedEnvironment(width, height)
        self.env.create_terrain_map(terrain_ratio) # ERRORE
        
        # Update planner and sensors
        self.planner = MultiPlanner(self.env)
        self.lidar = LidarSensor(self.env)
        
        # Reset simulation
        self.reset_simulation()
        
        # Set robot and goal positions
        start_x = self.start_x_var.get()
        start_y = self.start_y_var.get()
        goal_x = self.goal_x_var.get()
        goal_y = self.goal_y_var.get()
        
        # Ensure positions are valid
        if not self.env.is_valid_position(start_x, start_y):
            messagebox.showwarning("Invalid Position", "Start position is invalid (inside obstacle or out of bounds).")
            return
        
        if not self.env.is_valid_position(goal_x, goal_y):
            messagebox.showwarning("Invalid Position", "Goal position is invalid (inside obstacle or out of bounds).")
            return
        
        self.env.set_robot_pos(start_x, start_y)
        self.robot_pose = (start_x, start_y, 0)  # x, y, theta
        self.env.set_goal_pos(goal_x, goal_y)
        
        # Update display
        self.update_display()
        self.status_var.set("Environment generated")
        
    def plan_path(self):
        """
        Plan a path using the selected algorithm
        """
        algorithm = self.algorithm_var.get()
        optimize = self.optimize_var.get()
        
        self.status_var.set(f"Planning path using {algorithm}...")
        self.root.update()
        
        # Plan the path
        self.path = self.planner.plan(algorithm, optimize)
        
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
        
        # Reset robot position
        start_x = self.start_x_var.get()
        start_y = self.start_y_var.get()
        self.robot_pose = (start_x, start_y, 0)
        
        # Clear path
        self.path = None
        
        # Update display
        self.update_display()
        self.status_var.set("Simulation reset")
        self.simulate_button.config(text="Start Simulation")
        
    def run_simulation(self):
        """
        Run the simulation loop
        """
        # Reset to start position
        start_x = self.start_x_var.get()
        start_y = self.start_y_var.get()
        self.robot_pose = (start_x, start_y, 0)
        
        dt = 0.1  # Time step
        last_time = time.time()
        
        while self.running:
            # Calculate actual time step
            current_time = time.time()
            actual_dt = (current_time - last_time) * self.speed_var.get()
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
        
        # Draw the grid
        for y in range(self.env.height):
            for x in range(self.env.width):
                terrain_type = self.env.grid[y, x]
                color = TerrainType.color(terrain_type)
                if terrain_type != TerrainType.FREE:  # Only draw non-free cells
                    self.ax.add_patch(plt.Rectangle((x, y), 1, 1, color=color, alpha=0.7))
        
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
        
        # Draw LIDAR if enabled
        if self.show_lidar_var.get():
            scan_data = self.lidar.scan((x, y), np.degrees(theta))
            for angle_deg, distance in scan_data.items():
                angle_rad = np.radians(angle_deg)
                end_x = (x + 0.5) + distance * np.cos(angle_rad)
                end_y = (y + 0.5) + distance * np.sin(angle_rad)
                self.ax.plot([x + 0.5, end_x], [y + 0.5, end_y], 'g-', alpha=0.3, linewidth=0.5)
        
        # Draw goal
        if self.env.goal_pos:
            goal_x, goal_y = self.env.goal_pos
            self.ax.add_patch(plt.Circle((goal_x + 0.5, goal_y + 0.5), 0.4, color='green', alpha=0.7))
        
        # Set grid and labels
        self.ax.grid(True, linestyle='--', alpha=0.6)
        self.ax.set_title(f"Robot Path Planning Simulation")
        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Y")
        
        # Update the canvas
        self.canvas.draw()
