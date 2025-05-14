# Robot Path Planning Simulation

This project implements a path planning simulation for robots using Python and integrates with Arduino for physical robot control. The system enables optimal path planning in environments with obstacles using algorithms like A* and RRT, providing visualizations and animations of robot movement.

## Project Structure

The project is organized into modules following object-oriented design principles and software development best practices:

```
.
├── config/               # Configuration files
├── data/                 # Simulation data
├── docs/                 # Documentation
├── scripts/              # Utility scripts
├── src/                  # Source code
│   ├── environment/      # Environment simulation management
│   ├── planning/         # Path planning algorithms
│   ├── robot/            # Robot simulation and sensors
│   ├── visualization/    # Visualization and rendering
│   └── communication/    # Arduino interface
├── tests/                # Unit tests
├── main.py               # Main entry point
├── requirements.txt      # Python dependencies
└── README.md             # Documentation
```

## Main Components

### Environment

The `environment` module manages the simulation environment representation:
- 2D grid with free cells and obstacles
- Robot and goal positioning
- Position validity checking

### Path Planning

The `planning` module implements algorithms for path planning:
- **A\* (A-star)**: Search algorithm that finds the optimal path by minimizing a cost function
- **RRT** (Rapidly-exploring Random Tree): Algorithm that efficiently explores the space by building a tree of configurations

### Robot

The `robot` module implements:
- Robot movement simulation
- Virtual sensors for obstacle detection
- Speed and orientation control

### Visualization

The `visualization` module provides:
- Environment and obstacle visualization
- Robot movement animation
- Path graphs and statistics

### Communication

The `communication` module manages:
- Serial interface with Arduino
- Command transmission protocol
- Sensor feedback reception

## A* Path Planning Algorithm

The A* algorithm is an informed search algorithm that finds the optimal path between two points. The algorithm combines:

1. **Path cost**: Distance already traveled from the start node
2. **Heuristic**: Estimated distance remaining to the goal

For each node, A* calculates:
```
f(n) = g(n) + h(n)
```
where:
- `g(n)` is the path cost from the start node to node `n`
- `h(n)` is the heuristic that estimates the cost from node `n` to the goal

The algorithm uses a priority queue to explore nodes with the lowest `f(n)` value, ensuring the optimality of the found path when the heuristic is admissible (does not overestimate the actual cost).

## Arduino Integration

The project supports integration with Arduino robots through serial communication:

1. **Path Planning**: The A* algorithm calculates the optimal path
2. **Path Translation**: The path is converted into movement commands for the motors
3. **Command Transmission**: Commands are sent to the robot via serial connection
4. **Feedback**: The robot sends sensor information to verify position and detect unexpected obstacles

The communication protocol includes:
- `PATH_LEN:n` - Specifies the path length
- `PATH_POINT:i,x,y` - Defines the coordinates of the i-th point
- `PATH_FOLLOW` - Starts following the path

## Usage

### Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

### Execution

To start the simulation:
```
python main.py
```

Available options:
```
python main.py --width 30 --height 30 --robot-x 5 --robot-y 5 --goal-x 25 --goal-y 25
```

To test the Arduino connection:
```
python scripts/test_arduino.py --port /dev/ttyUSB0 --baud 9600
```

## Future Extensions

The project can be extended with:

1. **Advanced algorithms**: Implementation of RRT*, D*, Theta* to compare performance in different scenarios
2. **Dynamic mapping**: Real-time map updates based on sensor readings
3. **Advanced control**: PID control implementation for smoother movements
4. **User interface**: Development of a GUI for interaction with the simulation
5. **Multirobots**: Extension to support multiple robots simultaneously
