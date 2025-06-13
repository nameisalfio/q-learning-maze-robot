from lib.dds.dds import *
from lib.system import *
from lib.utils import *
from lib.data.dataplot import *
from lib.system.cart import *
from lib.system.controllers import *
from lib.system.trajectory import *
from lib.system.polar import *
from lib.dds.dds import *
from lib.utils.time import *
from enum import Enum
import math
import time

class PolarWheelSpeedControl:
    """Wheel speed control for differential drive robot."""
    
    def __init__(self, _wheelbase, _kp, _ki, _kd, _sat):
        self.wheelbase = _wheelbase
        self.left_pid = PID_Controller(_kp, _ki, _kd, _sat)
        self.right_pid = PID_Controller(_kp, _ki, _kd, _sat)
        
    def evaluate(self, delta_t, target_linear, target_angular, current_left, current_right):
        """Calculate wheel torques based on target velocities."""
        self.target_left = target_linear - (target_angular * self.wheelbase) / 2.0
        self.target_right = target_linear + (target_angular * self.wheelbase) / 2.0
        out_left = self.left_pid.evaluate(delta_t, self.target_left - current_left)
        out_right = self.right_pid.evaluate(delta_t, self.target_right - current_right)
        return (out_left, out_right)

DIRECTIONS = {
    "UP": 0,
    "DOWN": 1,
    "LEFT": 2,
    "RIGHT": 3
}

class MoveResult(Enum):
    """Enumeration for movement results."""
    SUCCESS = "success"           # Movement completed successfully
    COLLISION = "collision"       # Collision with wall detected
    GOAL_REACHED = "goal_reached" # Goal area reached
    TIMEOUT = "timeout"           # Movement timed out
    CHECKPOINT_REACHED = "checkpoint_reached" # Checkpoint reached

class DiffDriveRoboticAgent:
    """Differential drive robot agent for maze navigation."""
    
    def __init__(self, dds, time):
        self.time = time
        self.dds = dds
        
        # Initialize DDS communication
        self.dds.start()
        self.dds.subscribe(["Collision", "GoalReached", "tick", "checkpoint_reached"])
        self.dds.publish('reset_checkpoints', 0, DDS.DDS_TYPE_INT)

        # Control systems
        self.wheel_speed_control = PolarWheelSpeedControl(
            _wheelbase=0.5,
            _kp=0.8,
            _ki=0.0,
            _kd=0.0,
            _sat=10.0
        )

        self.robot = TwoWheelsCart2DEncodersOdometry(
            _mass=1.0,
            _radius=0.3,
            _lin_friction=0.8,
            _ang_friction=0.7,
            _r_traction_left=0.04,
            _r_traction_right=0.04,
            _traction_wheelbase=0.4,
            _r_encoder_left=0.03,
            _r_encoder_right=0.03,
            _encoder_wheelbase=0.5,
            _encoder_ticks=4096
        )

        self.polar_controller = Polar2DController(
            KP_linear=1.4,
            v_max=1.7,     
            KP_heading=2.0,   
            w_max=2.0         
        )

        self.virtual_robot = None
        self.target_tolerance = 0.001  # Tolerance for reaching target position
        self.last_checkpoint_reached = None

    def stop_robot(self):
        """Stop robot movement immediately."""
        self.robot.evaluate(0.008, 0.0, 0.0)
        
        # Publish current position
        pose = self.robot.get_pose()
        self.dds.publish('X', pose[0], DDS.DDS_TYPE_FLOAT)
        self.dds.publish('Y', pose[1], DDS.DDS_TYPE_FLOAT)
        self.dds.publish('Theta', pose[2], DDS.DDS_TYPE_FLOAT)

    def _backup_from_collision(self, start_pos, collision_pos):
        """Execute backup maneuver after collision."""
        print("Executing collision recovery backup")
        backup_target_x = start_pos[0]
        backup_target_y = start_pos[1]
        
        print(f"Backup target: ({backup_target_x:.2f}, {backup_target_y:.2f})")
        
        # Create virtual robot for backup
        backup_virtual_robot = StraightLine2DMotion(0.8, 1.0, 1.0)
        backup_virtual_robot.start_motion(
            (collision_pos[0], collision_pos[1]), 
            (backup_target_x, backup_target_y)
        )
        
        # Execute backup movement
        max_backup_iterations = 900
        backup_iteration = 0
        
        while backup_iteration < max_backup_iterations:
            godot_delta = self.dds.read('tick')
            time.sleep(0.052)
            backup_iteration += 1

            # Generate target from backup virtual robot
            (x_target, y_target) = backup_virtual_robot.evaluate(godot_delta)
            
            # Control robot during backup
            pose = self.robot.get_pose()
            (target_v, target_w) = self.polar_controller.evaluate(godot_delta, x_target, y_target, pose)
            
            (current_left, current_right) = self.robot.get_wheel_speed()
            (torque_left, torque_right) = self.wheel_speed_control.evaluate(godot_delta, 
                                                                    target_v, target_w, 
                                                                    current_left, current_right)
            
            self.robot.evaluate(godot_delta, torque_left, torque_right)
            
            # Publish position during backup
            pose = self.robot.get_pose()
            self.dds.publish('X', pose[0], DDS.DDS_TYPE_FLOAT)
            self.dds.publish('Y', pose[1], DDS.DDS_TYPE_FLOAT)
            self.dds.publish('Theta', pose[2], DDS.DDS_TYPE_FLOAT)

            distance_to_target = math.sqrt((pose[0] - backup_target_x)**2 + (pose[1] - backup_target_y)**2)
            if distance_to_target < self.target_tolerance:
                print(f"Target raggiunto: ({pose[0]:.2f}, {pose[1]:.2f})")
                break
        
        self.stop_robot()

    def move(self, direction):
        """Execute movement in specified direction."""
        if direction not in DIRECTIONS:
            raise ValueError("Invalid direction. Use 'UP', 'DOWN', 'LEFT', or 'RIGHT'.")

        # Initialize motion planning
        self.virtual_robot = StraightLine2DMotion(1.2, 1.8, 1.8)

        current_pose = self.robot.get_pose()
        start_x = current_pose[0]
        start_y = current_pose[1]
        start_pos = (start_x, start_y)

        # Calculate target position (10.5 unit movement)
        if direction == "UP":
            target_x, target_y = start_x, start_y + 10.5
        elif direction == "DOWN":
            target_x, target_y = start_x, start_y - 10.5
        elif direction == "LEFT":
            target_x, target_y = start_x - 10.5, start_y
        elif direction == "RIGHT":
            target_x, target_y = start_x + 10.5, start_y

        self.virtual_robot.start_motion((start_x, start_y), (target_x, target_y))
        print(f"Moving {direction} from ({start_x:.2f}, {start_y:.2f}) to ({target_x:.2f}, {target_y:.2f})")
        
        max_iterations = 900
        iteration = 0

        # Wait for Godot tick
        self.dds.wait('tick')

        while iteration < max_iterations:
            godot_delta = self.dds.read('tick')
            time.sleep(0.052)
            iteration += 1

            # Check for goal reached
            goal_reached = self.dds.read("GoalReached")
            if goal_reached == 1:
                print("Goal reached!")
                self.stop_robot()
                return MoveResult.GOAL_REACHED, None

            # Check for collision
            collision = self.dds.read("Collision")
            if collision == 1:
                print(f"\033[91mCollision detected! Status: {collision}.\033[0m")

                # Get collision position
                collision_pose = self.robot.get_pose()
                collision_pos = (collision_pose[0], collision_pose[1])
                
                # Execute backup and wait for completion
                self._backup_from_collision(start_pos, collision_pos)
                
                print("Collision resolved with backup procedure.")
                return MoveResult.COLLISION, None

            # Generate target from virtual robot
            (x_target, y_target) = self.virtual_robot.evaluate(godot_delta)

            # Robot control
            pose = self.robot.get_pose()
            (target_v, target_w) = self.polar_controller.evaluate(godot_delta, x_target, y_target, pose)
            
            (current_left, current_right) = self.robot.get_wheel_speed()
            (torque_left, torque_right) = self.wheel_speed_control.evaluate(godot_delta, 
                                                                    target_v, target_w, 
                                                                    current_left, current_right)

            self.robot.evaluate(godot_delta, torque_left, torque_right)
            
            # Publish position
            pose = self.robot.get_pose()
            self.dds.publish('X', pose[0], DDS.DDS_TYPE_FLOAT)
            self.dds.publish('Y', pose[1], DDS.DDS_TYPE_FLOAT)
            self.dds.publish('Theta', pose[2], DDS.DDS_TYPE_FLOAT)

            # Check if target reached
            distance_to_target = math.sqrt((pose[0] - target_x)**2 + (pose[1] - target_y)**2)
            if distance_to_target < self.target_tolerance:
                print(f"Target reached: ({pose[0]:.2f}, {pose[1]:.2f})")
                break

        # Check for timeout
        if iteration >= max_iterations:
            print(f"Timeout reached after {max_iterations} iterations")
            self.stop_robot()
            return MoveResult.TIMEOUT, None
        
        # Check if checkpoint reached
        checkpoint_reached = self.dds.read("checkpoint_reached")
        if checkpoint_reached != 0 and checkpoint_reached is not None and self.last_checkpoint_reached != checkpoint_reached:
            self.last_checkpoint_reached = checkpoint_reached
            print("=" * 50)
            print(f"\033[92mCHECKPOINT REACHED: {checkpoint_reached}\033[0m")
            print("=" * 50)
            return MoveResult.CHECKPOINT_REACHED, checkpoint_reached

        # Movement completed successfully
        self.stop_robot()
        return MoveResult.SUCCESS, None

    def get_current_position(self):
        """Get current robot position."""
        pose = self.robot.get_pose()
        return (pose[0], pose[1], pose[2])
    
    def reset(self):
        """Reset robot state."""
        self.stop_robot()
        self.virtual_robot = None
        self.last_checkpoint_reached = 0
        self.robot.reset()
        self.dds.publish('X', 0.0, DDS.DDS_TYPE_FLOAT)
        self.dds.publish('Y', 0.0, DDS.DDS_TYPE_FLOAT)
        self.dds.publish('Theta', 0.0, DDS.DDS_TYPE_FLOAT)
        print("Robot state reset.")