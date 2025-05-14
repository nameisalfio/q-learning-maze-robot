import numpy as np

class DifferentialDriveModel:
    """
    Differential drive kinematic model for wheeled robots
    """
    def __init__(self, wheel_radius=0.1, axle_length=0.5):
        self.wheel_radius = wheel_radius
        self.axle_length = axle_length
        
    def forward_kinematics(self, left_wheel_velocity, right_wheel_velocity):
        """
        Calculate linear and angular velocities from wheel velocities
        
        Parameters:
            left_wheel_velocity: Angular velocity of the left wheel
            right_wheel_velocity: Angular velocity of the right wheel
            
        Returns:
            (linear_velocity, angular_velocity) tuple
        """
        # Linear velocity (forward speed)
        linear_velocity = self.wheel_radius * (left_wheel_velocity + right_wheel_velocity) / 2
        
        # Angular velocity (turning rate)
        angular_velocity = self.wheel_radius * (right_wheel_velocity - left_wheel_velocity) / self.axle_length
        
        return linear_velocity, angular_velocity
        
    def inverse_kinematics(self, linear_velocity, angular_velocity):
        """
        Calculate wheel velocities from linear and angular velocities
        
        Parameters:
            linear_velocity: Forward speed
            angular_velocity: Turning rate
            
        Returns:
            (left_wheel_velocity, right_wheel_velocity) tuple
        """
        # Left wheel velocity
        left_wheel_velocity = (linear_velocity - angular_velocity * self.axle_length / 2) / self.wheel_radius
        
        # Right wheel velocity
        right_wheel_velocity = (linear_velocity + angular_velocity * self.axle_length / 2) / self.wheel_radius
        
        return left_wheel_velocity, right_wheel_velocity
        
    def update_pose(self, pose, left_wheel_velocity, right_wheel_velocity, dt):
        """
        Update the robot's pose based on wheel velocities
        
        Parameters:
            pose: (x, y, theta) tuple where theta is in radians
            left_wheel_velocity: Angular velocity of the left wheel
            right_wheel_velocity: Angular velocity of the right wheel
            dt: Time step
            
        Returns:
            Updated (x, y, theta) pose
        """
        x, y, theta = pose
        
        # Calculate linear and angular velocities
        v, omega = self.forward_kinematics(left_wheel_velocity, right_wheel_velocity)
        
        # Update pose
        if abs(omega) < 1e-6:  # Moving in straight line
            x = x + v * np.cos(theta) * dt
            y = y + v * np.sin(theta) * dt
            # theta remains unchanged
        else:  # Following a circular arc
            # Angle rotated
            dtheta = omega * dt
            theta = theta + dtheta
            
            # Distance traveled
            if abs(omega) > 1e-6:
                radius = v / omega
                x = x + radius * (np.sin(theta) - np.sin(theta - dtheta))
                y = y - radius * (np.cos(theta) - np.cos(theta - dtheta))
            else:
                x = x + v * np.cos(theta) * dt
                y = y + v * np.sin(theta) * dt
            
            # Normalize theta to [-pi, pi]
            theta = np.arctan2(np.sin(theta), np.cos(theta))
            
        return x, y, theta
