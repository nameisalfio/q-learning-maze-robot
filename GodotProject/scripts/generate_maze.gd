extends Node3D

@export var maze_width: int = 10
@export var maze_height: int = 10
@export var cell_size: float = 3.5
@export var wall_height: float = 2.5
@export var wall_thickness: float = 0.3

var maze = []
var visited = []

func _ready():
	generate_maze()
	build_floor()
	build_maze()

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
	var floor = MeshInstance3D.new()
	floor.mesh = PlaneMesh.new()
	floor.mesh.size = Vector2(maze_width * cell_size, maze_height * cell_size)

	var floor_material = StandardMaterial3D.new()
	floor_material.albedo_color = Color(0.75, 0.85, 0.75) # verde salvia chiaro

	floor.material_override = floor_material
	floor.transform.origin = Vector3((maze_width * cell_size) / 2 - cell_size / 2, 0, (maze_height * cell_size) / 2 - cell_size / 2)
	add_child(floor)

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

func _place_wall(position: Vector3, size: Vector3, material: Material):
	var wall_body = StaticBody3D.new()
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
