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

class PolarWheelSpeedControl:
    def __init__(self, _wheelbase, _kp, _ki, _kd, _sat):
        self.wheelbase = _wheelbase
        self.left_pid = PID_Controller(_kp, _ki, _kd, _sat)
        self.right_pid = PID_Controller(_kp, _ki, _kd, _sat)
        
    def evaluate(self, delta_t, target_linear, target_angular, current_left, current_right):
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

# Enum per i risultati del movimento
class MoveResult(Enum):
    SUCCESS = "success"           # Movimento completato con successo
    COLLISION = "collision"       # Collisione con muro
    GOAL_REACHED = "goal_reached" # Uscita raggiunta
    TIMEOUT = "timeout"           # Timeout del movimento

class DiffDriveRoboticAgent:
    def __init__(self, dds, time):
        self.time = time
        self.dds = dds
        
        # Subscribe ai topic necessari per RL
        self.dds.subscribe(["Collision", "GoalReached"])

        self.wheel_speed_control = PolarWheelSpeedControl(
            _wheelbase=0.5,
            _kp=0.6,
            _ki=0.0,
            _kd=0.0,
            _sat=8.0
        )

        self.robot = TwoWheelsCart2DEncodersOdometry(
            _mass=1.0,
            _radius=0.3,
            _lin_friction=0.9,
            _ang_friction=0.8,
            _r_traction_left=0.04,
            _r_traction_right=0.04,
            _traction_wheelbase=0.4,
            _r_encoder_left=0.03,
            _r_encoder_right=0.03,
            _encoder_wheelbase=0.5,
            _encoder_ticks=4096
        )

        self.polar_controller = Polar2DController(
            KP_linear=1.0,
            v_max=1.5,     
            KP_heading=2.0,   
            w_max=2.0         
        )

        self.virtual_robot = None

    def stop_robot(self):
        """Ferma immediatamente il robot"""
        # Imposta velocità zero
        self.robot.evaluate(0.016, 0.0, 0.0)
        
        # Pubblica posizione corrente
        pose = self.robot.get_pose()
        self.dds.publish('X', pose[0], DDS.DDS_TYPE_FLOAT)
        self.dds.publish('Y', pose[1], DDS.DDS_TYPE_FLOAT)
        self.dds.publish('Theta', pose[2], DDS.DDS_TYPE_FLOAT)

    def move(self, direction):
        """
        Esegue un movimento in una direzione.
        
        Returns:
            MoveResult: Il risultato del movimento
        """
        if direction not in DIRECTIONS:
            raise ValueError("Invalid direction. Use 'UP', 'DOWN', 'LEFT', or 'RIGHT'.")

        # Motion planning
        self.virtual_robot = StraightLine2DMotion(1.2, 1.8, 1.8)

        current_pose = self.robot.get_pose()
        start_x = current_pose[0]
        start_y = current_pose[1]

        if direction == "UP":
            target_x, target_y = start_x, start_y + 1
        elif direction == "DOWN":
            target_x, target_y = start_x, start_y - 1
        elif direction == "LEFT":
            target_x, target_y = start_x - 1, start_y
        elif direction == "RIGHT":
            target_x, target_y = start_x + 1, start_y

        original_target = (target_x, target_y)
        self.virtual_robot.start_motion((start_x, start_y), (target_x, target_y))
        
        print(f"Moving {direction} from ({start_x:.2f}, {start_y:.2f}) to ({target_x:.2f}, {target_y:.2f})")
        
        max_iterations = 800
        iteration = 0
        target_tolerance = 0.01  # Tolleranza per considerare il target raggiunto
        
        while iteration < max_iterations:
            # Aspetta il tick di Godot
            self.dds.wait('tick')
            godot_delta = self.dds.read('tick')
            
            iteration += 1

            # Controlla se il goal del labirinto è stato raggiunto
            goal_reached = self.dds.read("GoalReached")
            if goal_reached == 1:
                print("Goal reached! Maze completed!")
                self.stop_robot()
                return MoveResult.GOAL_REACHED

            # Controlla collisione
            collision = self.dds.read("Collision")
            time.sleep(0.05)

            if collision == 1:
                print("Collision detected! Stopping movement.")
                self.stop_robot()
                # Reset collision flag
                self.dds.publish("Collision", 0, DDS.DDS_TYPE_INT)
                print(f"\033[91mCollision status: {collision}\033[0m")
                return MoveResult.COLLISION

            # Genera il target dal virtual robot
            (x_target, y_target) = self.virtual_robot.evaluate(godot_delta)

            # Controllo del robot
            pose = self.robot.get_pose()
            (target_v, target_w) = self.polar_controller.evaluate(godot_delta, x_target, y_target, pose)
            
            (current_left, current_right) = self.robot.get_wheel_speed()
            (torque_left, torque_right) = self.wheel_speed_control.evaluate(godot_delta, 
                                                                    target_v, target_w, 
                                                                    current_left, current_right)

            self.robot.evaluate(godot_delta, torque_left, torque_right)
            
            # Pubblica posizione
            pose = self.robot.get_pose()
            self.dds.publish('X', pose[0], DDS.DDS_TYPE_FLOAT)
            self.dds.publish('Y', pose[1], DDS.DDS_TYPE_FLOAT)
            self.dds.publish('Theta', pose[2], DDS.DDS_TYPE_FLOAT)

            # Log periodico
            if iteration % 20 == 0:
                distance = math.sqrt((pose[0] - original_target[0])**2 + (pose[1] - original_target[1])**2)
                #print(f"Iter {iteration}: at ({pose[0]:.2f}, {pose[1]:.2f}), dist to target: {distance:.3f}")

            # Controllo distanza dal target
            distance_to_target = math.sqrt((pose[0] - target_x)**2 + (pose[1] - target_y)**2)
            if distance_to_target < target_tolerance:
                print(f"Target reached with tolerance: ({pose[0]:.2f}, {pose[1]:.2f})")
                break

        # Timeout raggiunto
        if iteration >= max_iterations:
            print(f"Movement timeout after {max_iterations} iterations")
            self.stop_robot()
            return MoveResult.TIMEOUT

        # Movimento completato con successo
        self.stop_robot()
        return MoveResult.SUCCESS

    def get_current_position(self):
        """Restituisce la posizione corrente del robot"""
        pose = self.robot.get_pose()
        return (pose[0], pose[1], pose[2])

    def reset_flags(self):
        """Reset dei flag DDS"""
        self.dds.publish("Collision", 0, DDS.DDS_TYPE_INT)
        self.dds.publish("GoalReached", 0, DDS.DDS_TYPE_INT)