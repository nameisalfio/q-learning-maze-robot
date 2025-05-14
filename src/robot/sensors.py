import numpy as np

class VirtualSensor:
    """
    Base class for virtual sensors.
    """
    def __init__(self, environment, noise_level=0.0):
        self.env = environment
        self.noise_level = noise_level
    
    def add_noise(self, value):
        """Adds Gaussian noise to the value"""
        if self.noise_level <= 0:
            return value
        noise = np.random.normal(0, self.noise_level)
        return value + noise

class DistanceSensor(VirtualSensor):
    """
    Virtual distance sensor.
    Simulates a sensor that measures the distance to obstacles.
    """
    def __init__(self, environment, max_range=5, noise_level=0.1):
        super().__init__(environment, noise_level)
        self.max_range = max_range
    
    def measure_distance(self, pos, direction):
        """
        Measures the distance to the nearest obstacle in the specified direction.
        
        Args:
            pos (tuple): Position (x, y) to measure from
            direction (tuple): Direction (dx, dy) to measure in
            
        Returns:
            float: Measured distance, up to max_range
        """
        if not (0 <= pos[0] < self.env.width and 0 <= pos[1] < self.env.height):
            return 0  # Out of bounds
        
        x, y = pos
        dx, dy = direction
        
        # Normalize direction vector
        norm = np.sqrt(dx**2 + dy**2)
        if norm == 0:
            return self.max_range
        
        dx, dy = dx/norm, dy/norm
        
        # Check for each step
        distance = 0
        while distance < self.max_range:
            x += dx * 0.1
            y += dy * 0.1
            distance += 0.1
            
            # Round to grid position
            grid_x, grid_y = int(x), int(y)
            
            # Check if out of bounds
            if not (0 <= grid_x < self.env.width and 0 <= grid_y < self.env.height):
                break
            
            # Check if hit an obstacle
            if self.env.grid[grid_y, grid_x] == 1:
                break
        
        return self.add_noise(min(distance, self.max_range))
    
    def scan_surroundings(self, pos, angles=None):
        """
        Performs a 360-degree scan around the specified position.
        
        Args:
            pos (tuple): Position (x, y) to scan from
            angles (list): List of angles (in degrees) to scan (default: 8 directions)
            
        Returns:
            dict: Dictionary with angles and measured distances
        """
        if angles is None:
            angles = np.linspace(0, 360, 8, endpoint=False)
        
        scan_results = {}
        for angle in angles:
            # Convert angle to radians and calculate direction
            rad = np.radians(angle)
            direction = (np.cos(rad), np.sin(rad))
            
            # Measure distance in this direction
            distance = self.measure_distance(pos, direction)
            scan_results[angle] = distance
        
        return scan_results
