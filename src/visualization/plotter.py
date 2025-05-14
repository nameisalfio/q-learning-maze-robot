import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle, Circle

class EnvironmentPlotter:
    """
    Class for advanced environment visualization.
    Provides methods to visualize the environment, robot, and path.
    """
    def __init__(self, environment, figsize=(10, 8)):
        self.env = environment
        self.fig, self.ax = plt.subplots(figsize=figsize)
        self.path = None
        self.visited_nodes = None
    
    def set_path(self, path):
        """Sets the path to display"""
        self.path = path
    
    def set_visited_nodes(self, visited):
        """Sets the nodes visited during path search"""
        self.visited_nodes = visited
    
    def plot_environment(self):
        """Visualizes the environment with obstacles"""
        self.ax.clear()
        self.ax.set_xlim(0, self.env.width)
        self.ax.set_ylim(0, self.env.height)
        self.ax.set_aspect('equal')
        self.ax.set_title("Navigation Environment")
        
        # Draw grid
        for x in range(self.env.width + 1):
            self.ax.axvline(x, color='lightgray', linestyle='-', alpha=0.5)
        for y in range(self.env.height + 1):
            self.ax.axhline(y, color='lightgray', linestyle='-', alpha=0.5)
        
        # Draw obstacles
        for y in range(self.env.height):
            for x in range(self.env.width):
                if self.env.grid[y, x] == 1:
                    self.ax.add_patch(Rectangle((x, y), 1, 1, facecolor='black', alpha=0.7))
        
        # Draw nodes visited during search
        if self.visited_nodes:
            visited_x = [node[0] + 0.5 for node in self.visited_nodes]
            visited_y = [node[1] + 0.5 for node in self.visited_nodes]
            self.ax.scatter(visited_x, visited_y, color='lightblue', alpha=0.5, s=30)
        
        # Draw planned path
        if self.path:
            path_x = [pos[0] + 0.5 for pos in self.path]
            path_y = [pos[1] + 0.5 for pos in self.path]
            self.ax.plot(path_x, path_y, 'b-', linewidth=2.5, alpha=0.8)
        
        # Draw robot
        if self.env.robot_pos:
            self.ax.add_patch(Circle((self.env.robot_pos[0] + 0.5, self.env.robot_pos[1] + 0.5), 
                                    radius=0.4, facecolor='red', edgecolor='darkred', alpha=0.8))
        
        # Draw goal
        if self.env.goal_pos:
            self.ax.add_patch(Circle((self.env.goal_pos[0] + 0.5, self.env.goal_pos[1] + 0.5), 
                                    radius=0.4, facecolor='green', edgecolor='darkgreen', alpha=0.8))
        
        # Add axis labels
        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Y")
        
        return self.fig, self.ax
    
    def show(self):
        """Shows the visualization"""
        self.plot_environment()
        plt.tight_layout()
        plt.show()
    
    def save(self, filename):
        """Saves the visualization to file"""
        self.plot_environment()
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"Visualization saved to {filename}")
