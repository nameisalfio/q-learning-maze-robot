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

class DiffDriveRoboticAgent:
    def __init__(self, dds, time):
        self.time = time
        self.dds = dds
        self.dds.subscribe(["Collision"])

        self.wheel_speed_control = PolarWheelSpeedControl(
            _wheelbase=0.5,  # Example wheelbase
            _kp=1.0,         # Proportional gain
            _ki=0.0,         # Integral gain
            _kd=0.0,         # Derivative gain
            _sat=10.0        # Saturation limit
        )

        self.robot = TwoWheelsCart2DEncodersOdometry(
            _mass=1.0,  # 1 kg
            _radius=0.3,  # 30 cm radius
            _lin_friction=0.9,
            _ang_friction=0.8,
            _r_traction_left=0.04,  # 4 cm
            _r_traction_right=0.04,  # 4 cm
            _traction_wheelbase=0.4,  # 40 cm
            _r_encoder_left=0.03,  # 3 cm
            _r_encoder_right=0.03,  # 3 cm
            _encoder_wheelbase=0.5,  # 50 cm
            _encoder_ticks=4096  # resolution in ticks/rev
        )

        self.polar_controller = Polar2DController(
            KP_linear=4,  # Proportional gain for position control
            v_max=4.0,  # Maximum linear velocity in m/s
            KP_heading=8,  # Proportional gain for angular control
            w_max=6.0  # Maximum angular velocity in rad/s
        )

        self.virtual_robot = None

        self.current_x = 0.0
        self.current_y = 0.0
        self.current_theta = 0.0

    def reset(self):
        current_x = 0.0
        current_y = 0.0
        current_theta = 0.0
        self.dds.publish("X", current_x, DDS.DDS_TYPE_FLOAT)
        self.dds.publish("Y", current_y, DDS.DDS_TYPE_FLOAT)
        self.dds.publish("Theta", current_theta, DDS.DDS_TYPE_FLOAT)

    def move(self, direction):
        if direction not in DIRECTIONS:
            raise ValueError("Invalid direction. Use 'UP', 'DOWN', 'LEFT', or 'RIGHT'.")

        self.virtual_robot = StraightLine2DMotion(1.0, 1.5, 1.5)

        current_pose = self.robot.get_pose()
        target_x = start_x = current_pose[0]
        target_y = start_y = current_pose[1]
        current_theta = current_pose[2]

        if direction == "UP":
            target_y = start_y + 1
        elif direction == "DOWN":
            target_y = start_y - 1
        elif direction == "LEFT":
            target_x = start_x - 1
        elif direction == "RIGHT":
            target_x = start_x + 1

        self.virtual_robot.start_motion((start_x, start_y), (target_x, target_y))
        self.time.start()
        while self.time.get() < 5.0:
            self.time.sleep(0.005)
            delta_t = self.time.elapsed()

            collision_happened = self.dds.read("Collision")
            if collision_happened == 1:
                print("Collision detected!")
                self.time.start()
                current_x, current_y = self.robot.get_pose()[:2]
                self.virtual_robot.start_motion((current_x, current_y), (current_x, current_y))
                self.dds.publish("Collision", 0, DDS.DDS_TYPE_INT)
                break

            (x_target, y_target) = self.virtual_robot.evaluate(delta_t)
    
            pose = self.robot.get_pose()
            (target_v, target_w) = self.polar_controller.evaluate(delta_t, x_target, y_target, pose)
            
            (current_left, current_right) = self.robot.get_wheel_speed()
            (torque_left, torque_right) = self.wheel_speed_control.evaluate(delta_t, 
                                                                    target_v, target_w, 
                                                                    current_left, current_right )

            self.robot.evaluate(delta_t, torque_left, torque_right)
            
            pose = self.robot.get_pose()
            self.dds.publish('X', pose[0], DDS.DDS_TYPE_FLOAT)
            self.dds.publish('Y', pose[1], DDS.DDS_TYPE_FLOAT)
            self.dds.publish('Theta', pose[2], DDS.DDS_TYPE_FLOAT)