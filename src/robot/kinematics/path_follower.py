import numpy as np

class PathFollower:
    """
    Controller for following a path with a differential drive robot
    """
    def __init__(self, drive_model, look_ahead_distance=1.5):
        self.drive_model = drive_model
        self.look_ahead_distance = look_ahead_distance
        self.path = None
        self.current_target_idx = 0
        
    def set_path(self, path):
        """
        Set the path to follow
        """
        self.path = path
        self.current_target_idx = 0
        
    def update(self, pose, dt, max_linear_velocity=0.5, max_angular_velocity=np.pi/4):
        """
        Update the controller and calculate control inputs
        
        Parameters:
            pose: (x, y, theta) tuple
            dt: Time step
            max_linear_velocity: Maximum linear velocity
            max_angular_velocity: Maximum angular velocity
            
        Returns:
            (left_wheel_velocity, right_wheel_velocity, reached_goal) tuple
        """
        if not self.path or self.current_target_idx >= len(self.path):
            return 0, 0, True  # No path or already at the end
            
        x, y, theta = pose
        
        # Find the next target point along the path
        target_idx = self._find_target_point(x, y)
        self.current_target_idx = target_idx
        
        # If reached the end of the path
        if target_idx >= len(self.path) - 1:
            # Go to the last point
            target_x, target_y = self.path[-1]
            
            # If close enough to the goal, stop
            distance_to_goal = np.sqrt((target_x - x)**2 + (target_y - y)**2)
            if distance_to_goal < 0.5:  # Threshold for reaching the goal
                return 0, 0, True
        else:
            target_x, target_y = self.path[target_idx]
        
        # Calculate desired heading to the target
        desired_theta = np.arctan2(target_y - y, target_x - x)
        
        # Calculate error in heading
        theta_error = desired_theta - theta
        # Normalize to [-pi, pi]
        theta_error = np.arctan2(np.sin(theta_error), np.cos(theta_error))
        
        # Calculate distance to target
        distance = np.sqrt((target_x - x)**2 + (target_y - y)**2)
        
        # Simple proportional controller for heading
        k_theta = 1.0  # Proportional gain for heading
        
        # Calculate angular velocity based on heading error
        angular_velocity = k_theta * theta_error
        
        # Limit angular velocity
        angular_velocity = np.clip(angular_velocity, -max_angular_velocity, max_angular_velocity)
        
        # Calculate linear velocity based on distance and heading error
        # Reduce speed when turning sharply
        linear_velocity = max_linear_velocity * np.exp(-2 * abs(theta_error))
        
        # Limit linear velocity
        linear_velocity = np.clip(linear_velocity, 0, max_linear_velocity)
        
        # Calculate wheel velocities
        left_velocity, right_velocity = self.drive_model.inverse_kinematics(
            linear_velocity, angular_velocity)
            
        # Return control commands and a flag indicating if goal is reached
        return left_velocity, right_velocity, False
        
    def _find_target_point(self, x, y):
        """
        Find the index of the path point that is closest to the look-ahead distance
        """
        # Start from the current target index
        current_idx = max(0, self.current_target_idx)
        
        # Find the first point that is at least look_ahead_distance away
        while current_idx < len(self.path) - 1:
            target_x, target_y = self.path[current_idx]
            distance = np.sqrt((target_x - x)**2 + (target_y - y)**2)
            
            if distance >= self.look_ahead_distance:
                return current_idx
                
            current_idx += 1
            
        # If no point is far enough, return the last point
        return len(self.path) - 1
