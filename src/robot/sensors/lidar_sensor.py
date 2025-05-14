import numpy as np
import matplotlib.pyplot as plt

class LidarSensor:
    """
    Simulated LIDAR sensor that provides distance measurements in multiple directions
    """
    def __init__(self, environment, num_rays=36, max_range=15.0, noise_level=0.1):
        self.env = environment
        self.num_rays = num_rays
        self.max_range = max_range
        self.noise_level = noise_level
        
    def scan(self, position, orientation_deg=0):
        """
        Perform a LIDAR scan from the given position and orientation
        
        Parameters:
            position: (x, y) tuple
            orientation_deg: Orientation in degrees
            
        Returns:
            Dictionary mapping angles to distances
        """
        scan_data = {}
        
        for i in range(self.num_rays):
            # Calculate angle in degrees
            angle_deg = (i * 360 / self.num_rays + orientation_deg) % 360
            
            # Convert to radians
            angle_rad = np.radians(angle_deg)
            
            # Calculate direction vector
            direction = (np.cos(angle_rad), np.sin(angle_rad))
            
            # Measure distance
            distance = self._measure_distance(position, direction)
            
            # Add noise
            if self.noise_level > 0:
                noise = np.random.normal(0, self.noise_level * distance)
                distance = max(0, distance + noise)
                
            scan_data[angle_deg] = min(distance, self.max_range)
            
        return scan_data
        
    def _measure_distance(self, position, direction):
        """
        Measure distance to the nearest obstacle in the given direction
        """
        x, y = position
        dx, dy = direction
        
        # Step size for ray casting (smaller = more accurate but slower)
        step_size = 0.1
        
        # Cast ray until hitting an obstacle or reaching max range
        distance = 0
        while distance < self.max_range:
            # Update position along ray
            x += dx * step_size
            y += dy * step_size
            distance += step_size
            
            # Round to grid coordinates
            grid_x, grid_y = int(round(x)), int(round(y))
            
            # Check if position is out of bounds
            if not (0 <= grid_x < self.env.width and 0 <= grid_y < self.env.height):
                break
                
            # Check if position is an obstacle
            if not self.env.is_valid_position(grid_x, grid_y):
                return distance
                
        return self.max_range
        
    def visualize_scan(self, position, scan_data, ax=None):
        """
        Visualize LIDAR scan as lines radiating from position
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(8, 8))
            ax.set_xlim(0, self.env.width)
            ax.set_ylim(0, self.env.height)
            
        x, y = position
        
        for angle_deg, distance in scan_data.items():
            # Convert to radians
            angle_rad = np.radians(angle_deg)
            
            # Calculate end point
            end_x = x + distance * np.cos(angle_rad)
            end_y = y + distance * np.sin(angle_rad)
            
            # Draw line
            ax.plot([x, end_x], [y, end_y], 'g-', alpha=0.3)
            
        # Mark the sensor position
        ax.plot(x, y, 'ro')
        
        return ax