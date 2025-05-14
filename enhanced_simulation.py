#!/usr/bin/env python3
"""
Enhanced Robot Path Planning Simulation

This script runs an advanced path planning simulation with terrain types,
realistic kinematics, and multiple planning algorithms.
"""

import sys
import argparse
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Circle, Rectangle

from src.environment.enhanced_environment import EnhancedEnvironment
from src.environment.models.terrain import TerrainType
from src.planning.multi_planner import MultiPlanner
from src.robot.kinematics.differential_drive import DifferentialDriveModel
from src.robot.kinematics.path_follower import PathFollower
from src.robot.sensors.lidar_sensor import LidarSensor
from src.planning.algorithms.path_optimizer import PathOptimizer

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Enhanced Robot Path Planning Simulation")
    parser.add_argument("--width", type=int, default=50, help="Environment width")
    parser.add_argument("--height", type=int, default=50, help="Environment height")
    parser.add_argument("--terrain", type=float, default=0.15, help="Terrain ratio (0.0 to 1.0)")
    parser.add_argument("--algorithm", type=str, default="a_star", choices=["a_star", "rrt", "rrt_star"], help="Path planning algorithm")
    parser.add_argument("--optimize", action="store_true", help="Enable path optimization")
    parser.add_argument("--robot-x", type=int, default=2, help="Robot initial X position")
    parser.add_argument("--robot-y", type=int, default=2, help="Robot initial Y position")
    parser.add_argument("--goal-x", type=int, default=45, help="Goal X position")
    parser.add_argument("--goal-y", type=int, default=45, help="Goal Y position")
    parser.add_argument("--gui", action="store_true", help="Launch GUI instead of command-line simulation")
    return parser.parse_args()

def main():
    """Main function"""
    args = parse_arguments()
    
    # If GUI flag is set, launch the GUI
    if args.gui:
        launch_gui()
        return 0
    
    # Create enhanced environment
    env = EnhancedEnvironment(args.width, args.height)
    
    # Generate random terrain
    env.create_terrain_map(args.terrain)
    
    # Set robot and goal positions
    if not env.set_robot_pos(args.robot_x, args.robot_y):
        print(f"Could not position robot at ({args.robot_x}, {args.robot_y}). Invalid position.")
        return 1
    
    if not env.set_goal_pos(args.goal_x, args.goal_y):
        print(f"Could not set goal at ({args.goal_x}, {args.goal_y}). Invalid position.")
        return 1
    
    # Create path planner
    planner = MultiPlanner(env)
    
    # Plan the path
    print(f"Planning path using {args.algorithm}...")
    path = planner.plan(args.algorithm, args.optimize)
    
    if not path:
        print("Could not find a path!")
        return 1
    
    print(f"Path found with {len(path)} points")
    
    # Create robot models
    drive_model = DifferentialDriveModel()
    path_follower = PathFollower(drive_model)
    path_follower.set_path(path)
    
    # Create sensor
    lidar = LidarSensor(env)
    
    # Create figure for visualization
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # Initial robot pose
    robot_pose = (args.robot_x, args.robot_y, 0)  # x, y, theta
    
    # Setup for animation
    robot_circle = None
    robot_direction = None
    lidar_lines = []
    
    def init():
        """Initialize the animation"""
        nonlocal robot_circle, robot_direction, lidar_lines
        
        # Clear the axis
        ax.clear()
        
        # Set limits
        ax.set_xlim(0, env.width)
        ax.set_ylim(0, env.height)
        
        # Draw the grid
        for y in range(env.height):
            for x in range(env.width):
                terrain_type = env.grid[y, x]
                color = TerrainType.color(terrain_type)
                if terrain_type != TerrainType.FREE:  # Only draw non-free cells
                    ax.add_patch(Rectangle((x, y), 1, 1, color=color, alpha=0.7))
        
        # Draw the path
        path_x = [p[0] + 0.5 for p in path]
        path_y = [p[1] + 0.5 for p in path]
        ax.plot(path_x, path_y, 'b-', linewidth=2, alpha=0.7)
        
        # Draw the robot
        x, y, theta = robot_pose
        robot_circle = Circle((x + 0.5, y + 0.5), 0.4, color='red', alpha=0.7)
        ax.add_patch(robot_circle)
        
        # Draw direction indicator
        endx = (x + 0.5) + 0.4 * np.cos(theta)
        endy = (y + 0.5) + 0.4 * np.sin(theta)
        robot_direction, = ax.plot([x + 0.5, endx], [y + 0.5, endy], 'k-', linewidth=2)
        
        # LIDAR visualization
        scan_data = lidar.scan((x, y), np.degrees(theta))
        lidar_lines = []
        for angle_deg, distance in scan_data.items():
            angle_rad = np.radians(angle_deg)
            end_x = (x + 0.5) + distance * np.cos(angle_rad)
            end_y = (y + 0.5) + distance * np.sin(angle_rad)
            line, = ax.plot([x + 0.5, end_x], [y + 0.5, end_y], 'g-', alpha=0.3, linewidth=0.5)
            lidar_lines.append(line)
        
        # Draw goal
        goal_x, goal_y = env.goal_pos
        ax.add_patch(Circle((goal_x + 0.5, goal_y + 0.5), 0.4, color='green', alpha=0.7))
        
        # Set grid and labels
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.set_title(f"Robot Path Planning Simulation - {args.algorithm}")
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        
        return [robot_circle, robot_direction] + lidar_lines
    
    def update(frame):
        """Update the animation for each frame"""
        nonlocal robot_pose, robot_circle, robot_direction, lidar_lines
        
        # Update robot pose
        left_vel, right_vel, reached_goal = path_follower.update(robot_pose, 0.1)
        
        if reached_goal:
            # Stop animation
            ani.event_source.stop()
            print("Goal reached!")
            return [robot_circle, robot_direction] + lidar_lines
        
        # Update pose
        robot_pose = drive_model.update_pose(robot_pose, left_vel, right_vel, 0.1)
        x, y, theta = robot_pose
        
        # Update robot position
        robot_circle.center = (x + 0.5, y + 0.5)
        
        # Update direction indicator
        endx = (x + 0.5) + 0.4 * np.cos(theta)
        endy = (y + 0.5) + 0.4 * np.sin(theta)
        robot_direction.set_data([x + 0.5, endx], [y + 0.5, endy])
        
        # Update LIDAR visualization
        scan_data = lidar.scan((x, y), np.degrees(theta))
        for i, (angle_deg, distance) in enumerate(scan_data.items()):
            angle_rad = np.radians(angle_deg)
            end_x = (x + 0.5) + distance * np.cos(angle_rad)
            end_y = (y + 0.5) + distance * np.sin(angle_rad)
            if i < len(lidar_lines):
                lidar_lines[i].set_data([x + 0.5, end_x], [y + 0.5, end_y])
        
        return [robot_circle, robot_direction] + lidar_lines
    
    # Create animation
    ani = animation.FuncAnimation(fig, update, frames=1000, 
                                 init_func=init, blit=True, interval=50)
    
    plt.tight_layout()
    plt.show()
    
    return 0

def launch_gui():
    """Launch the GUI application"""
    import tkinter as tk
    from src.visualization.gui.simulation_gui import SimulationGUI
    
    root = tk.Tk()
    app = SimulationGUI(root)
    root.mainloop()

if __name__ == "__main__":
    sys.exit(main())
