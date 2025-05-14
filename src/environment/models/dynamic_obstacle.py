import numpy as np

class DynamicObstacle:
    """
    Class representing a moving obstacle
    """
    def __init__(self, x, y, width, height, velocity_x, velocity_y, environment):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.velocity_x = velocity_x
        self.velocity_y = velocity_y
        self.env = environment
        
    def update(self, dt):
        """
        Update obstacle position based on velocity and time step
        """
        # Calculate new position
        new_x = self.x + self.velocity_x * dt
        new_y = self.y + self.velocity_y * dt
        
        # Handle boundary collisions
        if new_x < 0 or new_x + self.width > self.env.width:
            self.velocity_x = -self.velocity_x
            new_x = self.x + self.velocity_x * dt
            
        if new_y < 0 or new_y + self.height > self.env.height:
            self.velocity_y = -self.velocity_y
            new_y = self.y + self.velocity_y * dt
            
        # Update the grid - first remove the obstacle from the old position
        for y in range(max(0, int(self.y)), min(self.env.height, int(self.y + self.height))):
            for x in range(max(0, int(self.x)), min(self.env.width, int(self.x + self.width))):
                self.env.grid[y, x] = 0  # Set to free space
                
        # Then add it at the new position
        for y in range(max(0, int(new_y)), min(self.env.height, int(new_y + self.height))):
            for x in range(max(0, int(new_x)), min(self.env.width, int(new_x + self.width))):
                self.env.grid[y, x] = 1  # Set to obstacle
                
        # Update obstacle position
        self.x = new_x
        self.y = new_y
        
    def get_position(self):
        """
        Get the current position of the obstacle
        """
        return int(self.x), int(self.y), int(self.width), int(self.height)
