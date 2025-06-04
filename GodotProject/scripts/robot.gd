extends Node3D

@onready var xy_text_edit = $"../CanvasGroup/XY"
@onready var theRobot = $"."

var x = 0.0
var y = 0.0
var theta = 0.0

func _ready():
	theRobot.add_to_group("robot")
	DDS.publish("GoalReached", DDS.DDS_TYPE_INT, 0)
	DDS.subscribe("X")
	DDS.subscribe("Y")
	DDS.subscribe("Theta")
	
	var area = $Area3D
	area.connect("body_entered", Callable(self, "_on_collision_with_wall"))

	_edit_xy_text(x, y)
	
func _on_collision_with_wall(body):
	if body.is_in_group("walls"):
		DDS.publish("Collision", DDS.DDS_TYPE_INT, 1)
		print("Collision!")

func _physics_process(_delta):
	pass
	
	#var prev_x = x
	#var prev_y = y
	#var prev_theta = theta

	#if collided:
	#	print("Collision! Movement reverted.")
	#	# Ripristina posizione e segnala collisione
	#	x = prev_x
	#	y = prev_y
	#	theta = prev_theta
	#	theRobot.global_position.x = x
	#	theRobot.global_position.z = -y
	#	theRobot.rotation.y = theta
	#	collided = false

	_edit_xy_text(x, y)

func _process(_delta):
	DDS.publish("tick", DDS.DDS_TYPE_FLOAT, _delta)
	
	var x = DDS.read("X")
	var y = DDS.read("Y")
	var theta = DDS.read("Theta")
	
	if (x != null)and(y != null)and(theta != null):
		theRobot.global_position.x = x
		theRobot.global_position.z = -y
		theRobot.global_rotation.y = theta
		
	# solo debug
	if Input.is_action_pressed("move_dx"):
		theRobot.global_position.x += 0.05
	elif Input.is_action_pressed("move_sx"):
		theRobot.global_position.x -= 0.05
	elif Input.is_action_pressed("move_up"):
		theRobot.global_position.z -= 0.05
	elif Input.is_action_pressed("move_down"):
		theRobot.global_position.z += 0.05
		
	_edit_xy_text(theRobot.global_position.x,theRobot.global_position.z)

func _edit_xy_text(x, y):
	xy_text_edit.text = "(%.2f, %.2f)" % [x,y]
