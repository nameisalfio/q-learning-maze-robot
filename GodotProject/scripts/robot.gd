extends Node3D

@onready var xy_text_edit = $"../CanvasGroup/XY"
@onready var theRobot = $"."

var x = 0.0
var y = 0.0
var theta = 0.0
var collision_wall = false

func _ready():
	theRobot.add_to_group("robot")
	DDS.subscribe("X")
	DDS.subscribe("Y")
	DDS.subscribe("Z")
	DDS.subscribe("Theta")
	
	var area = $Area3D
	area.connect("body_entered", Callable(self, "_on_collision_with_wall"))
	area.connect("body_exited", Callable(self, "_on_exit_from_wall"))

	_edit_xy_text(x, y)
	
func _on_exit_from_wall(body):
	if collision_wall == true:
		collision_wall = false
		DDS.publish("Collision", DDS.DDS_TYPE_INT, 0)
		print("No more collision!")
	
func _on_collision_with_wall(body):
	if body.is_in_group("walls"):
		collision_wall = true
		DDS.publish("Collision", DDS.DDS_TYPE_INT, 1)
		print("Collision!")

func robot_position_move(delta):
	var x = DDS.read("X")
	var y = DDS.read("Y")
	var z = DDS.read("Z")
	if z == null:
		z = 0
	var theta = DDS.read("Theta")
	
	theRobot.global_rotation = Vector3(0.0, 0.0, 0.0)
		
	if (x != null) and (y != null) and (z != null) and (theta != null):
		theRobot.global_position.x = x
		theRobot.global_position.z = -y
		theRobot.global_position.y = z
		theRobot.global_rotation.y = theta
		
	_edit_xy_text(theRobot.global_position.x,-theRobot.global_position.z)

func _physics_process(_delta):
	pass

func _process(_delta):
	# solo debug
	if Input.is_action_pressed("move_dx"):
		theRobot.global_position.x += 0.2
	elif Input.is_action_pressed("move_sx"):
		theRobot.global_position.x -= 0.2
	elif Input.is_action_pressed("move_up"):
		theRobot.global_position.z -= 0.2
	elif Input.is_action_pressed("move_down"):
		theRobot.global_position.z += 0.2
	
	# solo debug
	_edit_xy_text(theRobot.global_position.x,-theRobot.global_position.z)
	
	DDS.publish("tick", DDS.DDS_TYPE_FLOAT, _delta)
	robot_position_move(_delta)

func _edit_xy_text(x, y):
	xy_text_edit.text = "(%.2f, %.2f)" % [x,y]
