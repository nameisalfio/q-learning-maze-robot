extends Node3D

@export var maze_width: int = 10
@export var maze_height: int = 10
@export var cell_size: float = 3.5
@export var wall_height: float = 2.5
@export var wall_thickness: float = 0.3

# checkpoint già attivati
var activated_checkpoints = {}
var checkpoint_areas = {}
var reset_checkpoints = null
var prev_reset_checkpoints = null

var maze = []
var visited = []

func _ready():
	DDS.subscribe("reset_checkpoints")
	generate_maze()
	build_floor()
	build_maze()
	
func _process(delta):
	prev_reset_checkpoints = reset_checkpoints
	reset_checkpoints = DDS.read("reset_checkpoints")
	if reset_checkpoints != null and prev_reset_checkpoints != reset_checkpoints:
		print("Checkpoints reset: %d" % reset_checkpoints)
	
	if reset_checkpoints == 1:
		for i in range(1, 5):
			name = "checkpoint_%d" % i
			if activated_checkpoints[name] == true:
				activated_checkpoints[name] = false
				var area = checkpoint_areas[name]
				var mat = area.get_meta("material")
				mat.albedo_color = Color(0.95, 0.85, 0.6)  # verde acceso
				print("Checkpoint %s disattivato!" % name)
			DDS.publish("checkpoint_reached", DDS.DDS_TYPE_INT, 0)
			
func generate_maze():
	seed(1234)
	maze = []
	visited = []
	for y in maze_height:
		maze.append([])
		visited.append([])
		for x in maze_width:
			maze[y].append([true, true, true, true]) # N E S W walls
			visited[y].append(false)
	_dfs(Vector2i(0, 0))

	# Rimuove una parete per creare l'uscita (in basso a destra, lato est)
	maze[maze_height - 1][maze_width - 1][1] = false

func _dfs(pos: Vector2i):
	visited[pos.y][pos.x] = true
	var directions = [Vector2i(0, -1), Vector2i(1, 0), Vector2i(0, 1), Vector2i(-1, 0)] # N E S W
	directions.shuffle()
	for dir in directions:
		var nx = pos.x + dir.x
		var ny = pos.y + dir.y
		if nx >= 0 and nx < maze_width and ny >= 0 and ny < maze_height:
			if not visited[ny][nx]:
				if dir == Vector2i(0, -1):
					maze[pos.y][pos.x][0] = false
					maze[ny][nx][2] = false
				elif dir == Vector2i(1, 0):
					maze[pos.y][pos.x][1] = false
					maze[ny][nx][3] = false
				elif dir == Vector2i(0, 1):
					maze[pos.y][pos.x][2] = false
					maze[ny][nx][0] = false
				elif dir == Vector2i(-1, 0):
					maze[pos.y][pos.x][3] = false
					maze[ny][nx][1] = false
				_dfs(Vector2i(nx, ny))

func build_floor():
	var floor_body = StaticBody3D.new()
	floor_body.name = "MazeFloor"
	floor_body.collision_layer = 1
	floor_body.collision_mask = 1

	var floor_mesh = MeshInstance3D.new()
	var plane_mesh = PlaneMesh.new()
	plane_mesh.size = Vector2(maze_width * cell_size, maze_height * cell_size)
	floor_mesh.mesh = plane_mesh

	var floor_material = StandardMaterial3D.new()
	floor_material.albedo_color = Color(0.75, 0.85, 0.75) # verde salvia chiaro
	floor_mesh.material_override = floor_material

	# Posizione centrata
	var center_x = (maze_width * cell_size) / 2 - cell_size / 2
	var center_z = (maze_height * cell_size) / 2 - cell_size / 2
	floor_body.transform.origin = Vector3(center_x, 0, center_z)

	var collider = CollisionShape3D.new()
	var shape = BoxShape3D.new()
	shape.size = Vector3(maze_width * cell_size, 0.1, maze_height * cell_size)
	collider.shape = shape
	collider.transform.origin = Vector3(0, -0.05, 0) # leggermente sotto per evitare intersezioni

	floor_body.add_child(floor_mesh)
	floor_body.add_child(collider)
	add_child(floor_body)

func build_maze():
	var wall_size_h = Vector3(cell_size, wall_height, wall_thickness)
	var wall_size_v = Vector3(wall_thickness, wall_height, cell_size)

	var wall_material = StandardMaterial3D.new()
	wall_material.albedo_color = Color(0.85, 0.75, 0.6) # beige sabbia

	for y in maze_height:
		for x in maze_width:
			var cell = maze[y][x]
			var cx = x * cell_size
			var cz = y * cell_size
			if cell[0]: # North
				_place_wall(Vector3(cx, wall_height / 2, cz - cell_size / 2), wall_size_h, wall_material)
			if cell[1]: # East
				_place_wall(Vector3(cx + cell_size / 2, wall_height / 2, cz), wall_size_v, wall_material)
			if cell[2]: # South
				_place_wall(Vector3(cx, wall_height / 2, cz + cell_size / 2), wall_size_h, wall_material)
			if cell[3]: # West
				_place_wall(Vector3(cx - cell_size / 2, wall_height / 2, cz), wall_size_v, wall_material)
				
	var goal_pos = Vector3(maze_width * cell_size, 0, (maze_height - 1) * cell_size)
	create_goal_area(goal_pos)
	
	# Aggiungi i checkpoints
	for i in range(1, 4): # checkpoints da 1 a 3 sulla diagonale
		var px = int(i * maze_width / (5))
		var py = int(i * maze_height / (5))
		var position = Vector3(px * cell_size, 0, py * cell_size)
		create_checkpoint_area(i, position)
		
	create_checkpoint_area(4, Vector3(7.0, 0, 28.0))

func _place_wall(position: Vector3, size: Vector3, material: Material):
	var wall_body = StaticBody3D.new()
	wall_body.add_to_group("walls")
	wall_body.transform.origin = position
	wall_body.collision_layer = 1
	wall_body.collision_mask = 1

	var wall_mesh = MeshInstance3D.new()
	var mesh = BoxMesh.new()
	mesh.size = size
	mesh.material = material
	wall_mesh.mesh = mesh
	wall_body.add_child(wall_mesh)

	var collider = CollisionShape3D.new()
	var shape = BoxShape3D.new()
	shape.size = size
	collider.shape = shape
	wall_body.add_child(collider)

	add_child(wall_body)

func create_goal_area(position: Vector3):
	# Crea piattaforma su cui il robot può stare
	var platform = StaticBody3D.new()
	platform.transform.origin = position + Vector3(0, 0.01, 0)

	var p_mesh = MeshInstance3D.new()
	var p_box = BoxMesh.new()
	p_box.size = Vector3(cell_size, 0.1, cell_size)
	p_mesh.mesh = p_box

	var p_mat = StandardMaterial3D.new()
	p_mat.albedo_color = Color(0.6, 0.85, 0.9)
	p_mesh.material_override = p_mat
	platform.add_child(p_mesh)

	var p_col = CollisionShape3D.new()
	var p_shape = BoxShape3D.new()
	p_shape.size = Vector3(cell_size, 0.1, cell_size)
	p_col.shape = p_shape
	platform.add_child(p_col)

	add_child(platform)

	# Crea Area3D per rilevare il goal
	var goal_area = Area3D.new()
	goal_area.name = "GoalArea"
	goal_area.monitoring = true
	goal_area.collision_layer = 2
	goal_area.collision_mask = 1

	var g_shape = BoxShape3D.new()
	g_shape.size = Vector3(0.5, 1.0, 0.5)

	var g_col = CollisionShape3D.new()
	g_col.shape = g_shape

	goal_area.transform.origin = position + Vector3(0, 0, 0)
	goal_area.add_child(g_col)

	goal_area.connect("body_entered",
		Callable(self, "_on_goal_area_entered").bind(goal_area))

	add_child(goal_area)

func _on_goal_area_entered(body, area):
	print("Obiettivo raggiunto!")
	DDS.publish("GoalReached", DDS.DDS_TYPE_INT, 1)
		
func _on_checkpoint_entered(body, area):
	if body.is_in_group("robot"):
		var name = area.get_meta("name")  # es: "checkpoint_1"

		if not activated_checkpoints[name]:
			activated_checkpoints[name] = true
			var mat = area.get_meta("material")
			mat.albedo_color = Color(0.4, 1.0, 0.4)  # verde acceso
			print("Checkpoint %s attivato!" % name)

			# Estrai numero del checkpoint (dopo "_")
			var parts = name.split("_")
			var checkpoint_num = int(parts[-1])  # prende l'ultimo elemento

			print(checkpoint_num)
			DDS.publish("checkpoint_reached", DDS.DDS_TYPE_INT, checkpoint_num)
		
		
func create_checkpoint_area(index: int, position: Vector3):
	var checkpoint_name = "checkpoint_%d" % index
	activated_checkpoints[checkpoint_name] = false

	# --- CREA LA PIATTAFORMA ---
	var platform_body = StaticBody3D.new()
	platform_body.name = checkpoint_name + "_platform"
	platform_body.transform.origin = position + Vector3(0, 0.01, 0)

	var platform_mesh = MeshInstance3D.new()
	var mesh = BoxMesh.new()
	mesh.size = Vector3(cell_size, 0.1, cell_size)
	platform_mesh.mesh = mesh

	var material = StandardMaterial3D.new()
	material.albedo_color = Color(0.95, 0.85, 0.6)  # colore iniziale
	mesh.material = material
	platform_mesh.material_override = material

	platform_body.add_child(platform_mesh)
	add_child(platform_body)

	# --- CREA L'AREA DI CHECKPOINT ---
	var area = Area3D.new()
	area.name = checkpoint_name
	area.monitoring = true
	area.collision_layer = 2
	area.collision_mask = 1  # il robot ha layer 1

	var area_shape = BoxShape3D.new()
	area_shape.size = Vector3(0.3, 1.0, 0.3)
	var area_collider = CollisionShape3D.new()
	area_collider.shape = area_shape
	area_collider.transform.origin = Vector3(0, 0.5, 0)

	area.transform.origin = position + Vector3(0, 0.05, 0)
	area.add_child(area_collider)

	area.set_meta("material", material)
	area.set_meta("name", checkpoint_name)
	area.connect("body_entered", Callable(self, "_on_checkpoint_entered").bind(area))

	checkpoint_areas[checkpoint_name] = area
	add_child(area)
