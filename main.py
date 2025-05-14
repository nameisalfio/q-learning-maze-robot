#!/usr/bin/env python3
"""
Robot Path Planning Simulation

This script runs a path planning simulation for a robot in a 2D environment.
It uses the A* algorithm to find the optimal path while avoiding obstacles.
"""

import sys
import argparse
from src.environment.environment import Environment
from src.planning.path_planner import PathPlanner
from src.robot.robot_simulation import RobotSimulation
from src.visualization.plotter import EnvironmentPlotter

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Robot Path Planning Simulation")
    parser.add_argument("--width", type=int, default=20, help="Environment width")
    parser.add_argument("--height", type=int, default=20, help="Environment height")
    parser.add_argument("--config", type=str, help="Environment configuration file")
    parser.add_argument("--robot-x", type=int, default=2, help="Robot initial X position")
    parser.add_argument("--robot-y", type=int, default=2, help="Robot initial Y position")
    parser.add_argument("--goal-x", type=int, default=18, help="Goal X position")
    parser.add_argument("--goal-y", type=int, default=18, help="Goal Y position")
    parser.add_argument("--visualize-only", action="store_true", help="Visualization only, no animation")
    return parser.parse_args()

def main():
    """Main function"""
    # Parse arguments
    args = parse_arguments()
    
    # Create environment
    env = Environment(args.width, args.height)
    
    # Load from file if specified
    if args.config:
        if env.load_from_file(args.config):
            print(f"Environment loaded from {args.config}")
        else:
            print(f"Could not load environment from {args.config}, using default environment")
            # Add default obstacles
            env.add_obstacle(5, 5, 10, 2)    # Horizontal obstacle
            env.add_obstacle(5, 10, 2, 8)    # Vertical obstacle
            env.add_obstacle(12, 10, 3, 8)   # Another vertical obstacle
    else:
        # Add default obstacles
        env.add_obstacle(5, 5, 10, 2)    # Horizontal obstacle
        env.add_obstacle(5, 10, 2, 8)    # Vertical obstacle
        env.add_obstacle(12, 10, 3, 8)   # Another vertical obstacle
    
    # Set robot and goal positions
    if not env.set_robot_pos(args.robot_x, args.robot_y):
        print(f"Could not position robot at ({args.robot_x}, {args.robot_y}). Invalid position.")
        return 1
    
    if not env.set_goal_pos(args.goal_x, args.goal_y):
        print(f"Could not set goal at ({args.goal_x}, {args.goal_y}). Invalid position.")
        return 1
    
    # Create path planner
    planner = PathPlanner(env)
    
    if args.visualize_only:
        # Visualization only
        path = planner.a_star()
        if path:
            plotter = EnvironmentPlotter(env)
            plotter.set_path(path)
            plotter.show()
        else:
            print("Could not find a path!")
    else:
        # Simulation with animation
        sim = RobotSimulation(env, planner)
        if sim.plan_path():
            sim.run_simulation()
        else:
            print("Could not find a path!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
