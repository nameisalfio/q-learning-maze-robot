# Robot Path Planning Simulation

This project implements a path planning simulation for robots using Python and integrates with Arduino for physical robot control. The system enables optimal path planning in environments with obstacles using algorithms like A* and RRT, providing visualizations and animations of robot movement.

## Project Overview

The goal of this project is to create a system that allows an Arduino robot to autonomously navigate in an environment with obstacles. The project is divided into two main components:

1. **Python Simulation**: A virtual environment that simulates the robot's behavior and plans its path.
2. **Arduino Control**: An interface to communicate with a physical robot and make it follow the planned path.

## Theoretical Concepts

### Path Planning

Path planning is the process of determining an optimal path from a starting point to a goal point while avoiding obstacles. In this project, we primarily use the A* algorithm for this purpose.

#### A* Algorithm

A* is an informed search algorithm that combines:

- **g(n)**: The cost of the path from the start point to the current node n
- **h(n)**: A heuristic that estimates the cost from node n to the goal

For each node, A* calculates `f(n) = g(n) + h(n)` and always selects the node with the lowest f(n) value, thus ensuring an optimal path when the heuristic is admissible.

The A* process can be summarized as:
1. Initialize an open list with the start node
2. While the open list is not empty:
   - Select the node with the lowest f(n)
   - If it's the goal, you've found the optimal path
   - Otherwise, expand its neighbors and update them in the open list

#### Manhattan Distance

In our project, we use the Manhattan distance as a heuristic:
```
h(n) = |x1 - x2| + |y1 - y2|
```
This is an appropriate choice for grid-based environments where movement is limited to the four cardinal directions.

### Environment Representation

The environment is represented as a 2D grid where:
- `0` represents a free space
- `1` represents an obstacle

This simple yet effective representation allows for:
- Easy verification of obstacle presence
- Direct calculation of a node's neighbors
- Intuitive visualization of the environment

### Arduino Integration

Communication between Python and Arduino occurs via a serial connection. The communication protocol includes:

1. **Path Transmission**: Python sends the sequence of coordinates that form the optimal path
2. **Movement Control**: Arduino interprets these coordinates and controls the motors to follow the path
3. **Feedback**: Arduino sends sensor information to confirm position and detect unexpected obstacles

## Project Structure

The project is organized into modules following object-oriented design principles:

```
.
├── src/                  # Source code
│   ├── environment/      # Environment representation
│   ├── planning/         # Path planning algorithms
│   ├── robot/            # Robot simulation
│   ├── visualization/    # Environment visualization
│   └── communication/    # Arduino interface
├── scripts/              # Utility scripts
├── tests/                # Unit tests
└── main.py               # Program entry point
```

### Main Components

1. **Environment**: Manages the environment representation, including obstacles, robot position, and goal.
2. **PathPlanner**: Implements path planning algorithms, primarily A*.
3. **RobotSimulation**: Simulates robot movement and animates the visualization.
4. **ArduinoInterface**: Manages communication with Arduino for physical robot control.

## Future Extensions

The project can be extended in various directions:

1. **Advanced planning algorithms**: Implementation of RRT, D*, Theta* to compare performance in different scenarios.
2. **Dynamic mapping**: Real-time map updates based on sensor readings.
3. **Virtual sensors**: Simulation of sensors like LIDAR or ultrasonic for more realistic obstacle detection.
4. **Dynamic planning**: Path recalculation in the presence of moving or unexpected obstacles.
5. **Path optimization**: Implementation of smoothing algorithms to generate more natural paths.

## How to Use

To run the simulation:

```bash
python main.py
```

To customize the simulation, various options are available:

```bash
python main.py --width 30 --height 30 --robot-x 5 --robot-y 5 --goal-x 25 --goal-y 25
```

To test the Arduino connection:

```bash
python scripts/test_arduino.py --port /dev/ttyUSB0
```

## Conclusion

This project demonstrates the practical application of path planning algorithms in robotics, combining software simulation and hardware control. It provides a solid foundation for the development of more complex autonomous navigation systems.