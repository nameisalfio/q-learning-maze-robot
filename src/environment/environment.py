import numpy as np

class Environment:
    """
    Class representing the 2D environment in which the robot moves.
    Manages the grid with obstacles, robot position, and goal position.
    """
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = np.zeros((height, width))  # 0: free, 1: obstacle
        self.robot_pos = None
        self.goal_pos = None
    
    def add_obstacle(self, x, y, width, height):
        """Adds a rectangular obstacle"""
        x1, y1 = max(0, x), max(0, y)
        x2, y2 = min(self.width, x + width), min(self.height, y + height)
        self.grid[y1:y2, x1:x2] = 1
    
    def set_robot_pos(self, x, y):
        """Sets the initial robot position"""
        if 0 <= x < self.width and 0 <= y < self.height and self.grid[y, x] == 0:
            self.robot_pos = (x, y)
            return True
        return False
    
    def set_goal_pos(self, x, y):
        """Sets the goal position"""
        if 0 <= x < self.width and 0 <= y < self.height and self.grid[y, x] == 0:
            self.goal_pos = (x, y)
            return True
        return False
    
    def is_valid_position(self, x, y):
        """Checks if a position is valid (within grid bounds and not an obstacle)"""
        return 0 <= x < self.width and 0 <= y < self.height and self.grid[y, x] == 0
    
    def load_from_file(self, filename):
        """Loads a configuration from file"""
        try:
            self.grid = np.loadtxt(filename)
            self.height, self.width = self.grid.shape
            return True
        except Exception as e:
            print(f"Error loading file: {e}")
            return False
    
    def save_to_file(self, filename):
        """Saves the current configuration to file"""
        try:
            np.savetxt(filename, self.grid, fmt='%d')
            return True
        except Exception as e:
            print(f"Error saving file: {e}")
            return False
