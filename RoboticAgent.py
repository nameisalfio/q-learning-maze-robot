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
        self.dds.start()
        self.dds.subscribe(["Collision", "GoalReached", "tick"])

        self.wheel_speed_control = PolarWheelSpeedControl(
            _wheelbase=0.5,
            _kp=0.7,
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
            KP_linear=1.2,
            v_max=1.5,     
            KP_heading=2.0,   
            w_max=2.0         
        )

        self.virtual_robot = None
        self.backup_distance = 0.1  # Distanza di backup in metri

    def stop_robot(self):
        """Ferma immediatamente il robot"""
        # Imposta velocità zero
        self.robot.evaluate(0.008, 0.0, 0.0)
        
        # Pubblica posizione corrente
        pose = self.robot.get_pose()
        self.dds.publish('X', pose[0], DDS.DDS_TYPE_FLOAT)
        self.dds.publish('Y', pose[1], DDS.DDS_TYPE_FLOAT)
        self.dds.publish('Theta', pose[2], DDS.DDS_TYPE_FLOAT)

    def _backup_from_collision(self, start_pos, collision_pos):
        """Esegue un backup dalla posizione di collisione verso la posizione di partenza"""
        print(f"Ritorno leggermente sui miei passi a seguito della collisione")
        
        # Calcola la direzione opposta al movimento
        dx = start_pos[0] - collision_pos[0]
        dy = start_pos[1] - collision_pos[1]
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance > 0:
            # Normalizza e scala per la distanza di backup
            backup_dx = (dx / distance) * self.backup_distance
            backup_dy = (dy / distance) * self.backup_distance
        else:
            # Se siamo alla posizione di partenza, backup nella direzione opposta all'heading
            current_pose = self.robot.get_pose()
            backup_dx = -self.backup_distance * math.cos(current_pose[2])
            backup_dy = -self.backup_distance * math.sin(current_pose[2])
        
        # Calcola target di backup
        backup_target_x = collision_pos[0] + backup_dx
        backup_target_y = collision_pos[1] + backup_dy
        
        print(f"Backup target: ({backup_target_x:.2f}, {backup_target_y:.2f})")
        
        # Crea un virtual robot per il backup
        backup_virtual_robot = StraightLine2DMotion(0.8, 1.0, 1.0)  # Più lento per il backup
        backup_virtual_robot.start_motion(
            (collision_pos[0], collision_pos[1]), 
            (backup_target_x, backup_target_y)
        )
        
        # Esegui il backup
        max_backup_iterations = 200
        backup_iteration = 0
        
        while backup_iteration < max_backup_iterations:
            godot_delta = self.dds.read('tick')
            time.sleep(0.052)

            backup_iteration += 1

            # Genera target dal virtual robot di backup
            (x_target, y_target) = backup_virtual_robot.evaluate(godot_delta)
            
            # Controllo del robot per backup
            pose = self.robot.get_pose()
            (target_v, target_w) = self.polar_controller.evaluate(godot_delta, x_target, y_target, pose)
            
            (current_left, current_right) = self.robot.get_wheel_speed()
            (torque_left, torque_right) = self.wheel_speed_control.evaluate(godot_delta, 
                                                                    target_v, target_w, 
                                                                    current_left, current_right)
            
            self.robot.evaluate(godot_delta, torque_left, torque_right)
            
            # Pubblica posizione durante backup
            pose = self.robot.get_pose()
            self.dds.publish('X', pose[0], DDS.DDS_TYPE_FLOAT)
            self.dds.publish('Y', pose[1], DDS.DDS_TYPE_FLOAT)
            self.dds.publish('Theta', pose[2], DDS.DDS_TYPE_FLOAT)
        
        self.stop_robot()

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
        start_pos = (start_x, start_y)  # Salva posizione di partenza

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
        target_tolerance = 0.005  # Tolleranza per considerare il target raggiunto
        
        # Aspetta il tick di Godot
        self.dds.wait('tick')

        while iteration < max_iterations:
            godot_delta = self.dds.read('tick')
            time.sleep(0.052)
            
            iteration += 1

            # Controlla se il goal del labirinto è stato raggiunto
            goal_reached = self.dds.read("GoalReached")
            if goal_reached == 1:
                print("Uscita raggiunta!")
                self.stop_robot()
                return MoveResult.GOAL_REACHED

            # Controlla collisione
            collision = self.dds.read("Collision")

            if collision == 1:
                print(f"\033[91mCollisione avvenuta! Stato: {collision}.\033[0m")

                # Ottieni posizione di collisione
                collision_pose = self.robot.get_pose()
                collision_pos = (collision_pose[0], collision_pose[1])
                
                # Esegui backup e attendi il completamento prima di proseguire
                self._backup_from_collision(start_pos, collision_pos)
                
                print("Collisione risolta con procedura di backup.")
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
                # print(f"Iter {iteration}: at ({pose[0]:.2f}, {pose[1]:.2f}), dist to target: {distance:.3f}")

            # Controllo distanza dal target
            distance_to_target = math.sqrt((pose[0] - target_x)**2 + (pose[1] - target_y)**2)
            if distance_to_target < target_tolerance:
                print(f"Target raggiunto: ({pose[0]:.2f}, {pose[1]:.2f})")
                break

        # Timeout raggiunto
        if iteration >= max_iterations:
            print(f"Timeout raggiunto dopo {max_iterations} iterazioni")
            self.stop_robot()
            return MoveResult.TIMEOUT

        # Movimento completato con successo
        self.stop_robot()
        return MoveResult.SUCCESS

    def get_current_position(self):
        """Restituisce la posizione corrente del robot"""
        pose = self.robot.get_pose()
        return (pose[0], pose[1], pose[2])