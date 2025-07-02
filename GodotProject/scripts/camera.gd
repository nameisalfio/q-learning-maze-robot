extends Camera3D

@export var robot: Node3D
@export var height: float = 30.0
@export var smooth_speed: float = 5.0
@export var zoom_speed: float = 60.0
@export var min_zoom: float = 2.0
@export var max_zoom: float = 300.0
@export var pitch_transition_speed := 3.0
@export var yaw_transition_speed := 3.0
@export var yaw_input_speed := 60.0

var target_pitch := -90.0
var current_pitch := -90.0
var target_yaw := 0.0
var current_yaw := 0.0
var tilted := false

func _ready():
	projection = PROJECTION_ORTHOGONAL
	size = height
	# at the beginning, the view is from above (-90 degrees orientation on the x axis)
	rotation_degrees = Vector3(current_pitch, target_yaw, 0)

func _process(delta):
	if robot:
		var target_pos = robot.global_transform.origin
		var desired_pos = Vector3(target_pos.x, target_pos.y + height, target_pos.z)
		global_transform.origin = global_transform.origin.lerp(desired_pos, delta * smooth_speed)

		if Input.is_action_pressed("zoom_in"):
			size = max(min_zoom, size - zoom_speed * delta)
		elif Input.is_action_pressed("zoom_out"):
			size = min(max_zoom, size + zoom_speed * delta)

	# tilt camera if key R is pressed
	if Input.is_action_just_pressed("tilt_camera"):
		tilted = not tilted
		target_pitch = -65.0 if tilted else -90.0
		
	# change the camera rotation on the y axis accordingly to the pressure of the left and right arrows
	if Input.is_action_just_pressed("rotate_camera_right"):
		target_yaw += 90.0

	if Input.is_action_just_pressed("rotate_camera_left"):
		target_yaw -= 90.0

	# interpolate pitch and yaw smoothly
	current_pitch = lerp(current_pitch, target_pitch, delta * pitch_transition_speed)
	current_yaw = lerp(current_yaw, target_yaw, delta * yaw_transition_speed)
	rotation_degrees = Vector3(current_pitch, current_yaw, 0)
