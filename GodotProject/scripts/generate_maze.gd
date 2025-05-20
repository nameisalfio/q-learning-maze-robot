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
	for i in range(4):
		var dir = directions[i]
		var nx = pos.x + dir.x
		var ny = pos.y + dir.y
		if nx >= 0 and nx < maze_width and ny >= 0 and ny < maze_height:
			if not visited[ny][nx]:
				# Remove wall between current and next cell
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
	var cube = BoxMesh.new()
	cube.size = Vector3(cell_size, wall_height, wall_thickness)

	var wall_material = StandardMaterial3D.new()
	wall_material.albedo_color = Color(0.85, 0.75, 0.6) # beige sabbia

	for y in maze_height:
		for x in maze_width:
			var cell = maze[y][x]
			var cx = x * cell_size
			var cz = y * cell_size
			if cell[0]: # North
				_place_wall(Vector3(cx, wall_height/2, cz - cell_size/2), 0, cube, wall_material)
			if cell[1]: # East
				_place_wall(Vector3(cx + cell_size/2, wall_height/2, cz), 90, cube, wall_material)
			if cell[2]: # South
				_place_wall(Vector3(cx, wall_height/2, cz + cell_size/2), 0, cube, wall_material)
			if cell[3]: # West
				_place_wall(Vector3(cx - cell_size/2, wall_height/2, cz), 90, cube, wall_material)

func _place_wall(position: Vector3, rot_y_deg: float, mesh: Mesh, material: Material):
	var wall = MeshInstance3D.new()
	wall.mesh = mesh
	wall.material_override = material
	wall.transform.origin = position
	wall.rotate_y(deg_to_rad(rot_y_deg))
	
	var collider = CollisionShape3D.new()
	var shape = BoxShape3D.new()
	shape.size = mesh.size
	collider.shape = shape
	wall.add_child(collider)

	add_child(wall)
