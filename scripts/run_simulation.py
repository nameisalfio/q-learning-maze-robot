#!/usr/bin/env python3
"""
Script to run the robot simulation
"""

import os
import sys

# Add main directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.environment.environment import Environment
from src.planning.path_planner import PathPlanner
from src.robot.robot_simulation import RobotSimulation

def main():
    # Create a 20x20 environment
    env = Environment(20, 20)
    
    # Add some obstacles
    env.add_obstacle(5, 5, 10, 2)    # Horizontal obstacle
    env.add_obstacle(5, 10, 2, 8)    # Vertical obstacle
    env.add_obstacle(12, 10, 3, 8)   # Another vertical obstacle
    
    # Set robot and goal positions
    env.set_robot_pos(2, 2)
    env.set_goal_pos(18, 18)
    
    # Create path planner
    planner = PathPlanner(env)
    
    # Create simulation
    sim = RobotSimulation(env, planner)
    
    # Plan and run
    if sim.plan_path():
        sim.run_simulation()
    else:
        print("Could not find a path!")

if __name__ == "__main__":
    main()
