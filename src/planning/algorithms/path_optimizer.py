import numpy as np
from scipy.interpolate import splprep, splev

class PathOptimizer:
    """
    Class for smoothing and optimizing paths
    """
    def __init__(self, environment):
        self.env = environment
        
    def smooth_path(self, path, smoothing=0.5, num_points=100, check_collision=True):
        """
        Smooth a path using B-spline interpolation
        
        Parameters:
            path: List of (x, y) tuples
            smoothing: Smoothing factor (0 = interpolate, larger values = smoother)
            num_points: Number of points in the output path
            check_collision: If True, check if the smoothed path hits obstacles
            
        Returns:
            Smoothed path as list of (x, y) tuples
        """
        if len(path) < 3:
            return path  # Not enough points to smooth
            
        # Extract x and y coordinates
        path_x = [p[0] for p in path]
        path_y = [p[1] for p in path]
        
        # Create spline parameters
        tck, u = splprep([path_x, path_y], s=smoothing, k=3)
        
        # Evaluate spline at equally spaced points
        u_new = np.linspace(0, 1, num_points)
        x_new, y_new = splev(u_new, tck)
        
        # Create smoothed path
        smoothed_path = []
        for i in range(len(x_new)):
            # Round to get integer coordinates
            x = int(round(x_new[i]))
            y = int(round(y_new[i]))
            
            # Ensure points are within bounds
            x = max(0, min(x, self.env.width - 1))
            y = max(0, min(y, self.env.height - 1))
            
            # Check for collisions if required
            if check_collision and not self.env.is_valid_position(x, y):
                # If collision detected, return original path
                print("Smoothed path collides with obstacles. Using original path.")
                return path
                
            smoothed_path.append((x, y))
            
        return smoothed_path
        
    def prune_path(self, path):
        """
        Remove redundant points from a path
        
        Returns:
            Pruned path with fewer points
        """
        if len(path) < 3:
            return path
            
        pruned_path = [path[0]]  # Start with the first point
        
        for i in range(1, len(path) - 1):
            prev_point = path[i-1]
            current_point = path[i]
            next_point = path[i+1]
            
            # Check if current point is redundant
            # A point is redundant if it's on a straight line between prev and next
            # and no obstacles between prev and next
            x1, y1 = prev_point
            x2, y2 = current_point
            x3, y3 = next_point
            
            # Check if points are collinear
            cross_product = abs((y2-y1)*(x3-x2) - (y3-y2)*(x2-x1))
            
            # If points are almost collinear and path is obstacle-free
            if cross_product < 0.01 and self._path_obstacle_free(prev_point, next_point):
                continue  # Skip current point
            
            pruned_path.append(current_point)
            
        pruned_path.append(path[-1])  # Add the last point
        return pruned_path
        
    def _path_obstacle_free(self, point1, point2):
        """
        Check if path between two points is obstacle-free
        """
        x1, y1 = point1
        x2, y2 = point2
        
        # Bresenham's line algorithm to check all cells along the line
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        
        while True:
            # Check current cell
            if not self.env.is_valid_position(x1, y1):
                return False
                
            # Check if reached the end
            if x1 == x2 and y1 == y2:
                break
                
            # Update position
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy
                
        return True
