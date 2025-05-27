extends Node3D

var theRobot
var left_motor : HingeJoint3D
var right_motor : HingeJoint3D
@onready var xy_text_edit = $"../CanvasGroup/XY"

# Called when the node enters the scene tree for the first time.
func _ready():
	#inizializzazione server
	theRobot = $"."
	DDS.subscribe("X")
	DDS.subscribe("Y")
	DDS.subscribe("Theta")
	
	#print(theRobot.global_position.x, " ", -theRobot.global_position.z, " ", theRobot.global_rotation.y)
	_edit_xy_text(theRobot.global_position.x, -theRobot.global_position.z)

func _physics_process(delta):
	pass


# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(_delta):
	#print(theRobot.global_position.x, " ", -theRobot.global_position.z, " ", theRobot.global_rotation.y)
	DDS.publish("tick", DDS.DDS_TYPE_FLOAT, _delta)

	var x = DDS.read("X")
	var y = DDS.read("Y")
	var theta = DDS.read("Theta")
	
	# solo per testare i collider
	if Input.is_action_pressed("move_dx"):
		theRobot.global_position.x += 0.05
	elif Input.is_action_pressed("move_sx"):
		theRobot.global_position.x -= 0.05
	elif Input.is_action_pressed("move_up"):
		theRobot.global_position.z -= 0.05
	elif Input.is_action_pressed("move_down"):
		theRobot.global_position.z += 0.05
	

	if (x != null)and(y != null)and(theta != null):
		theRobot.global_position.x = x
		theRobot.global_position.z = -y
		theRobot.global_rotation.y = theta

	_edit_xy_text(theRobot.global_position.x, -theRobot.global_position.z)


func _integrate_forces(state):
	pass

func _edit_xy_text(x, y):
	xy_text_edit.text = "(%.2f, %.2f)" % [x,y]
