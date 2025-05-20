extends Camera3D

@export var robot: Node3D
@export var height: float = 30.0
@export var smooth_speed: float = 5.0
@export var zoom_speed: float = 60.0
@export var min_zoom: float = 2.0
@export var max_zoom: float = 300.0

func _ready():
	projection = PROJECTION_ORTHOGONAL
	size = height
	# Fissa la rotazione per una vista dall'alto (top-down)
	rotation_degrees = Vector3(-90, -90, 0)

func _process(delta):
	if robot:
		var target_pos = robot.global_transform.origin
		var desired_pos = Vector3(target_pos.x, target_pos.y + height, target_pos.z)
		global_transform.origin = global_transform.origin.lerp(desired_pos, delta * smooth_speed)

		# Zoom dinamico
		if Input.is_action_pressed("zoom_in"):
			size = max(min_zoom, size - zoom_speed * delta)
		elif Input.is_action_pressed("zoom_out"):
			size = min(max_zoom, size + zoom_speed * delta)
