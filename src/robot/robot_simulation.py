import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib.animation as animation

class RobotSimulation:
    """
    Class for robot simulation.
    Manages visualization and animation of robot movement.
    """
    def __init__(self, environment, path_planner):
        self.env = environment
        self.planner = path_planner
        self.path = None
        self.current_pos_idx = 0
        
        # Create figure for visualization
        self.fig, self.ax = plt.subplots(figsize=(10, 8))
        self.robot_marker = None
        self.goal_marker = None
    
    def plan_path(self):
        """Plans the path using the path planning algorithm"""
        self.path = self.planner.a_star()
        self.current_pos_idx = 0
        return self.path is not None
    
    def setup_visualization(self):
        """Sets up the environment visualization"""
        self.ax.clear()
        self.ax.set_xlim(0, self.env.width)
        self.ax.set_ylim(0, self.env.height)
        self.ax.set_aspect('equal')
        self.ax.set_title("Robot Path Planning Simulation")
        
        # Draw obstacles
        for y in range(self.env.height):
            for x in range(self.env.width):
                if self.env.grid[y, x] == 1:
                    self.ax.add_patch(Rectangle((x, y), 1, 1, facecolor='black'))
        
        # Draw planned path
        if self.path:
            path_x = [pos[0] + 0.5 for pos in self.path]
            path_y = [pos[1] + 0.5 for pos in self.path]
            self.ax.plot(path_x, path_y, 'b--', linewidth=2, alpha=0.7)
        
        # Draw robot
        if self.env.robot_pos:
            self.robot_marker = self.ax.plot([self.env.robot_pos[0] + 0.5], [self.env.robot_pos[1] + 0.5], 'ro', markersize=15)[0]
        
        # Draw goal
        if self.env.goal_pos:
            self.goal_marker = self.ax.plot([self.env.goal_pos[0] + 0.5], [self.env.goal_pos[1] + 0.5], 'go', markersize=15)[0]
    
    def update(self, frame):
        """Updates the robot position for animation"""
        if self.path and self.current_pos_idx < len(self.path):
            current_pos = self.path[self.current_pos_idx]
            self.robot_marker.set_data([current_pos[0] + 0.5], [current_pos[1] + 0.5])
            self.current_pos_idx += 1
        return self.robot_marker,
    
    def run_simulation(self):
        """Runs the simulation with animation"""
        if not self.path:
            print("No path found. Cannot run simulation.")
            return
        
        self.setup_visualization()
        frames = len(self.path)
        ani = animation.FuncAnimation(self.fig, self.update, frames=frames, 
                                     interval=300, blit=True, repeat=False)
        plt.grid(True)
        plt.show()
