# 🤖 Q-Learning Maze Robot

A sophisticated reinforcement learning system for training a differential drive robot to navigate complex mazes. This project integrates a physics-based Godot simulation with an advanced Q-Learning agent featuring a dynamic, curiosity-driven exploration strategy.

> **Note**: This project is designed for research and educational purposes in autonomous navigation, combining a real-time robotics simulation with a robust RL training pipeline.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Godot](https://img.shields.io/badge/Godot-4.x-blue.svg)](https://godotengine.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/Code%20Style-Black-black.svg)](https://black.readthedocs.io)
[![Jupyter](https://img.shields.io/badge/Jupyter-Notebooks-orange.svg)](https://jupyter.org)

## 📋 Table of Contents

- [🤖 Q-Learning Maze Robot](#-q-learning-maze-robot)
  - [📋 Table of Contents](#-table-of-contents)
  - [🎯 Overview](#-overview)
  - [✨ Key Features](#-key-features)
    - [🧠 Machine Learning](#-machine-learning)
    - [🤖 Robotics \& Simulation](#-robotics--simulation)
    - [🛠️ Development \& Usability](#️-development--usability)
  - [🏗️ System Architecture](#️-system-architecture)
  - [🚀 Quick Start](#-quick-start)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
    - [Running the System](#running-the-system)
  - [🎮 Usage](#-usage)
    - [Interactive Menu](#interactive-menu)
    - [Command-Line Interface (for automation)](#command-line-interface-for-automation)
  - [⚙️ Configuration](#️-configuration)
    - [Example `config.yaml` for Curiosity Strategy](#example-configyaml-for-curiosity-strategy)
  - [📊 Analysis and Visualization](#-analysis-and-visualization)
  - [📁 Project Structure](#-project-structure)
  - [🤝 Contributing](#-contributing)
  - [📄 License](#-license)

## 🎯 Overview

This project implements a complete reinforcement learning pipeline for a robot navigating a maze. The core of the system is a **Q-Learning agent** that learns optimal paths through trial and error. It interacts with a **Godot Engine simulation** via a DDS (Data Distribution Service) communication layer, allowing for decoupled, real-time training and testing.

The agent's learning is guided by a **Curiosity-driven exploration strategy**, which dynamically adjusts its exploration rate based on state novelty. This encourages the robot to thoroughly explore the maze instead of getting stuck in local optima. The reward system is designed with **progressive checkpoints** to provide intermediate goals, making it feasible to solve large, complex mazes with sparse final rewards.

## ✨ Key Features

### 🧠 Machine Learning
- **Advanced Q-Learning**: Tabular Q-Learning with learning rate decay for fine-tuning.
- **Dynamic Curiosity Strategy**: Exploration is driven by state visitation counts and action novelty, making it highly effective for complex environments.
- **Progressive Checkpoint Rewards**: A sophisticated reward system that provides increasing bonuses for reaching sequential checkpoints, guiding the agent toward the final goal.
- **Loop Detection & Penalization**: Automatically penalizes repetitive, inefficient behavior.

### 🤖 Robotics & Simulation
- **Differential Drive Physics**: The agent controls a simulated robot with realistic two-wheeled physics.
- **Decoupled Architecture**: Python-based RL brain communicates with a Godot Engine simulation via a DDS layer.
- **Two Simulation Modes**:
  - **Training Mode**: A "teleport" mode for rapid, physics-less training episodes.
  - **Testing Mode**: A full physics simulation for realistic evaluation of the trained policy.
- **Collision Handling**: Automatic collision detection in the simulation environment.

### 🛠️ Development & Usability
- **Centralized Configuration**: A single, comprehensive `config.yaml` file to manage all parameters.
- **CLI & Interactive Modes**: Run training via command-line arguments for automation or use the interactive menu for experimentation.
- **Model Persistence**: Save and resume training progress, including the Q-table and strategy state.
- **Detailed Logging**: Formatted and detailed console output, with logs saved to file for later analysis.

## 🏗️ System Architecture

The system is composed of two main components that communicate in real-time:

1.  **The RL Agent (Python)**: This is the "brain" of the operation.
    - It runs the Q-Learning algorithm.
    - It implements the `CuriosityStrategy` to decide on actions.
    - It processes rewards from the environment to update its Q-table.
    - It sends movement commands and mode changes to the simulation.

2.  **The Simulation Environment (Godot Engine)**: This is the "body" and the world.
    - It renders the maze and the robot.
    - It handles physics simulation (in test mode).
    - It detects collisions, checkpoints, and goal events.
    - It sends sensor data (collision status, events) back to the agent.

This decoupled design allows for flexible development, where the learning logic is completely separate from the simulation environment.

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** with `pip`
- **Godot Engine 4.x**
- **Git** for cloning the repository

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-username/q-learning-maze-robot.git
cd q-learning-maze-robot

# 2. Install Python dependencies
pip install -r requirements.txt
```

### Running the System

1.  **Start the Godot Simulation**:
    - Open the Godot Engine.
    - Click `Import` or `Open Project` and select the `GodotProject/project.godot` file.
    - Once the project is open, press the **Play** button (▶️) in the top-right corner to start the simulation.

2.  **Launch the RL Agent**:
    - In your terminal, run the main Python script:
      ```bash
      python main.py
      ```

3.  **Begin Training**:
    - The script will present an interactive menu.
    - Select option `1` to start a new training session or `3` to continue from a saved model.
    - Watch the logs in your terminal as the agent learns!

## 🎮 Usage

The system can be operated in two ways:

### Interactive Menu

Run `python main.py` without arguments to access the menu:
- **1. 🎓 Train**: Start a new training run from scratch (will overwrite existing model).
- **2. 🧪 Test**: Evaluate the performance of the latest saved agent in a full physics simulation.
- **3. 📚 Continue**: Load the existing model and continue training.
- **4. 📊 Stats**: Display statistics of the saved model.
- **5. 🚪 Exit**: Close the program.

### Command-Line Interface (for automation)

You can run training or testing sessions directly from the command line, which is ideal for scripting.

```bash
# Continue training for 500 episodes
python main.py --mode continue --episodes 500

# Run a test with 10 episodes
python main.py --mode test --test_episodes 10

# Show agent statistics
python main.py --mode stats
```
Create a `run_training.sh` script for long, automated training sessions.

## ⚙️ Configuration

All system parameters are managed in `config.yaml`. This allows you to easily experiment with different settings without changing the code.

### Example `config.yaml` for Curiosity Strategy

```yaml
# Q-Learning Agent Parameters
agent:
  learning_rate: 0.12          # Initial learning rate
  min_learning_rate: 0.01      # Minimum learning rate after decay
  lr_decay: 0.997              # Multiplicative decay factor per episode
  discount_factor: 0.96        # Importance of future rewards

# Curiosity-Based Exploration Strategy
strategy:
  name: "curiosity"
  epsilon: 0.5                 # Base random exploration chance
  novelty_bonus: 5.0           # Bonus added to Q-values of less-tried actions

# Reward Structure
rewards:
  collision: -12.0
  goal_reached: 1000.0
  loop_penalty: -14.0

# Environment Configuration
environment:
  steps: 200                   # Max steps per episode before termination

# Training Configuration
training:
  episodes: 250                # Default number of episodes per training run
  save_every: 10               # Save the model every N episodes
  test_episodes: 8
  model_path: "models/q_agent.pkl"
```

## 📊 Analysis and Visualization

The project includes a Jupyter Notebook for plotting and analyzing training performance.

1.  **Launch Jupyter**:
    ```bash
    jupyter notebook
    ```
2.  **Open the Notebook**:
    - Navigate to and open `logs/plot_training_reward.ipynb`.
3.  **Run the Cells**:
    - The notebook will automatically find all `.log` files, parse the rewards, and generate an interactive plot showing:
      - Reward per episode.
      - A moving average to visualize the learning trend.

This is essential for understanding if the agent is consistently improving over time.

## 📁 Project Structure

```
q-learning-maze-robot/
├── config.yaml                    # Central configuration file
├── main.py                        # Main entry point for the system
├── README.md                      # This file
├── requirements.txt               # Python dependencies
├── GodotProject/                  # Godot Engine simulation project
├── lib/                           # Shared libraries (DDS, system utilities)
├── logs/                          # Stores training logs and analysis notebooks
│   └── plot_training_reward.ipynb
├── models/                        # Stores saved agent models (.pkl)
├── robot/                         # Robot control and DDS interface
│   └── robotic_agent.py
└── src/                           # Core RL components
    ├── agent.py                   # Q-Learning agent implementation
    ├── environment.py             # Environment logic and reward calculation
    ├── strategies.py              # Curiosity-driven exploration strategy
    └── trainer.py                 # Training and testing orchestrator
```

## 🤝 Contributing

Contributions are welcome! Whether it's a new feature, a bug fix, or improved documentation, please feel free to fork the repository and submit a pull request.

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.