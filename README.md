# 🤖 Q-Learning Maze Robot

A sophisticated reinforcement learning system for training differential drive robots to navigate complex mazes using Q-Learning with multiple exploration strategies.


> **Note**: This project combines robotics simulation in Godot Engine with advanced RL algorithms for autonomous navigation research.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Godot](https://img.shields.io/badge/Godot-4.x-blue.svg)](https://godotengine.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/Code%20Style-Black-black.svg)](https://black.readthedocs.io)
[![Jupyter](https://img.shields.io/badge/Jupyter-Notebooks-orange.svg)](https://jupyter.org)

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [Exploration Strategies](#-exploration-strategies)
- [Configuration](#-configuration)
- [Usage Examples](#-usage-examples)
- [Results and Analysis](#-results-and-analysis)
- [Architecture](#-architecture)
- [Contributing](#-contributing)
- [License](#-license)

## 🎯 Overview

This project implements a complete reinforcement learning pipeline for training robots in maze navigation tasks. The system features:

- **Real-time Simulation**: Integration with Godot Engine for physics-accurate robot simulation
- **Multiple RL Strategies**: Epsilon-Greedy, UCB, and Curiosity-based exploration
- **Progressive Reward System**: Encourages efficient navigation through streak bonuses
- **Comprehensive Analysis**: Jupyter notebooks for training visualization and performance analysis
- **Modular Architecture**: Easy to extend with new strategies and environments

### 🔬 Research Applications

- Autonomous navigation research
- Reinforcement learning algorithm comparison
- Robot behavior analysis
- Educational robotics and AI

## ✨ Features

### 🧠 Machine Learning
- **Q-Learning Algorithm**: Tabular Q-Learning with customizable parameters
- **Smart Exploration**: Multiple strategies for balancing exploration vs exploitation
- **Progressive Rewards**: Bonus system for consecutive successful moves
- **Loop Detection**: Automatic detection and penalization of repetitive behavior

### 🤖 Robotics
- **Differential Drive Control**: Realistic robot physics and control
- **Collision Handling**: Automatic collision detection and recovery
- **Real-time Communication**: DDS-based communication with Godot simulation
- **Position Tracking**: Precise odometry and state estimation

### 🛠️ Development
- **Single Configuration**: YAML-based configuration management
- **Comprehensive Logging**: Training progress and performance metrics
- **Model Persistence**: Save and load trained agents
- **Interactive Interface**: User-friendly training and testing interface

### 📊 Analysis
- **Jupyter Integration**: Rich visualization and analysis tools
- **Performance Metrics**: Success rate, reward progression, exploration coverage
- **Training Visualization**: Real-time plots of learning progress
- **Strategy Comparison**: Tools for comparing different exploration approaches

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** with pip
- **Godot Engine 4.x**
- **Git** for cloning the repository

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/q-learning-maze-robot.git
cd q-learning-maze-robot

# Install Python dependencies
pip install -r requirements.txt

# Optional: Install in development mode
pip install -e .
```

### Running the System

1. **Start Godot Simulation**:
   ```bash
   # Open Godot project
   godot GodotProject/project.godot
   
   # Or from Godot Editor: Open Project → Select GodotProject/
   # Then click Play to start the maze simulation
   ```

2. **Launch Q-Learning System**:
   ```bash
   python main.py
   ```

3. **Start Training**:
   - Select option `1` (Train)
   - Enter number of episodes (default: 200)
   - Watch the agent learn to navigate the maze!

### First Training Session

```bash
# Quick training with default settings
python main.py
# Choose: 1 → Enter → Wait for training completion

# Test the trained agent
# Choose: 2 → Enter → Watch the agent navigate
```

## 📁 Project Structure
```bash
q-learning-maze-robot/
├── README.md                      # This file
├── config.yaml                    # Central configuration file for all parameters 
├── main.py                        # Entry point for the Q-Learning system
├── requirements.txt               # Python dependencies 
├── .gitignore                     
├── GodotProject/                  # Godot Engine project files
│   ├── Components/                
│   ├── scripts/                   
│   └── project.godot              
├── src/                           # Core of the Q-Learning system
│   ├── __init__.py                
│   ├── agent.py                   # Q-Learning agent - learning, action selection, Q-table management
│   ├── environment.py             # Maze environment - state management, reward calculation, collision handling
│   ├── strategies.py              # Exploration strategies - Epsilon-Greedy, UCB, Curiosity
│   ├── trainer.py                 # Training orchestrator - episode loop, model saving
│   └── utils.py                   # Utilities - config manager, centralized logger
├── robot/                         # Physical robot interface
│   ├── __init__.py                
│   └── RoboticAgent.py            # Differential robot control - DDS, motion planning
├── notebooks/                     # Interactive analysis and testing
│   ├── __init__.py                  
│   └── robot_testing.ipynb        # Jupyter notebook - visualizations, movement testing
├── models/                        # Persistent trained models
│   └── .gitkeep                   
└── logs/                          # Training log files
  └── .gitkeep                   
```

### Key Components

| Component | Description |
|-----------|-------------|
| `src/agent.py` | Q-Learning agent implementation |
| `src/strategies.py` | Exploration strategies (Epsilon-Greedy, UCB, Curiosity) |
| `src/environment.py` | Maze environment and reward system |
| `src/trainer.py` | Training and testing orchestration |
| `robot/RoboticAgent.py` | Low-level robot control and communication |
| `config.yaml` | Single configuration file for all parameters |
| `notebooks/robot_testing.ipynb` | Analysis and visualization tools |
| `GodotProject/` | Godot simulation environment |

## 🧠 Exploration Strategies

The system supports three different exploration strategies, each with unique advantages:

### Epsilon-Greedy

**Description**: Classic strategy balancing exploration and exploitation with decaying randomness.

**Best for**: Good general-purpose strategy, simple and effective.

**Parameters**: `epsilon, epsilon_decay, epsilon_min`

**Configuration**:
```yaml
strategy:
  name: "epsilon_greedy"
```

### Upper Confidence Bound (UCB)

**Description**: Intelligent exploration prioritizing actions with high uncertainty.

**Best for**: When you want smarter exploration based on action confidence.

**Parameters**: `ucb_factor, epsilon`

**Configuration**:
```yaml
strategy:
  name: "ucb"
```

### Curiosity-Based

**Description**: Dynamic exploration driven by state novelty and visitation frequency.

**Best for**: Best for sparse reward environments, encourages thorough exploration.

**Parameters**: `base_epsilon, novelty_bonus`

**Configuration**:
```yaml
strategy:
  name: "curiosity"
```

### Strategy Comparison

| Strategy | Exploration Type | Learning Speed | Best Use Case |
|----------|------------------|----------------|---------------|
| Epsilon-Greedy | Random | Fast | General purpose, quick results |
| UCB | Uncertainty-based | Medium | When action confidence matters |
| Curiosity | Novelty-driven | Slow | Sparse rewards, thorough exploration |

## ⚙️ Configuration

All system parameters are configured through the single `config.yaml` file:

### Basic Configuration Structure

```yaml
# Main experiment settings
experiment:
  name: "q_learning_maze_robot"
  log_level: "INFO"

# Q-Learning parameters
agent:
  learning_rate: 0.1
  discount_factor: 0.95

# Exploration strategy
strategy:
  name: "epsilon_greedy"  # or "ucb" or "curiosity"
  # Strategy-specific parameters...

# Environment settings
environment:
  max_steps: 100
  collision_limit: 10

# Reward structure
rewards:
  success: 5.0
  collision: -10.0
  goal_reached: 100.0

# Training configuration
training:
  episodes: 200
  save_every: 50
```

### Strategy-Specific Examples

#### Epsilon_Greedy Strategy
```yaml
strategy:
  name: "epsilon_greedy"
  epsilon: 0.8
  epsilon_decay: 0.995
  epsilon_min: 0.1

training:
  episodes: 300
  save_every: 50

rewards:
  success: 5.0
  collision: -10.0
  goal_reached: 100.0
```

#### Ucb Strategy
```yaml
strategy:
  name: "ucb"
  ucb_factor: 2.0
  epsilon: 0.1

training:
  episodes: 200
  save_every: 25

environment:
  max_steps: 150
```

#### Curiosity Strategy
```yaml
strategy:
  name: "curiosity"
  epsilon: 0.3
  novelty_bonus: 5.0

rewards:
  exploration_bonus: 5.0
  success: 8.0

training:
  episodes: 400
```

### Key Parameters

| Parameter | Description | Default | Range |
|-----------|-------------|---------|-------|
| `agent.learning_rate` | Q-Learning update rate | 0.1 | 0.001-1.0 |
| `agent.discount_factor` | Future reward importance | 0.95 | 0.0-1.0 |
| `strategy.epsilon` | Random action probability | 0.8 | 0.0-1.0 |
| `rewards.success` | Reward for successful move | 5.0 | Any float |
| `training.episodes` | Number of training episodes | 200 | 1+ |

## 🎮 Usage Examples

### Basic Training
```bash
# Start Godot simulation first
# Open GodotProject/project.godot and run

# Run the Q-Learning system
python main.py

# Follow the interactive menu:
# 1. Train - Start training
# 2. Test - Evaluate agent
# 3. Continue - Resume training
# 4. Stats - View statistics
```

### Configuration Management
```bash
# Edit configuration
nano config.yaml

# Change strategy
sed -i 's/epsilon_greedy/ucb/' config.yaml

# Run with modified config
python main.py
```

### Analysis and Visualization
```bash
# Start Jupyter for analysis
jupyter notebook

# Open analysis notebook
# Navigate to notebooks/robot_testing.ipynb

# Run cells to analyze training results
```

## 📊 Results and Analysis

### Training Metrics

The system tracks comprehensive metrics during training:

- **Episode Rewards**: Total reward accumulated per episode
- **Success Rate**: Percentage of episodes reaching the goal
- **Steps per Episode**: Efficiency of navigation
- **Exploration Coverage**: Number of unique states visited
- **Strategy Parameters**: Evolution of exploration parameters

### Visualization Tools

#### Jupyter Notebook Analysis
```bash
jupyter notebook notebooks/robot_testing.ipynb
```

**Available Visualizations**:
- Training progress plots
- Success rate trends
- Q-value distribution analysis
- Robot trajectory visualization
- Strategy comparison charts


### Performance Benchmarks

Typical performance metrics for a well-trained agent:
| Metric | Epsilon-Greedy | UCB | Curiosity |
|--------|----------------|-----|-----------|
| Success Rate | - | - | - |
| Average Steps | - | - | - |
| Training Episodes | - | - | - |
| Exploration Coverage | - | - | - |

> **Note**: Results may vary based on maze complexity and configuration.

## 🤝 Contributing

We welcome contributions to improve the Q-Learning Maze Robot project!

### Contribution Guidelines

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Make** your changes following the coding standards
4. **Add** tests for new functionality
5. **Commit** changes: `git commit -m 'Add amazing feature'`
6. **Push** to branch: `git push origin feature/amazing-feature`
7. **Open** a Pull Request

### Code Standards

- **Python Style**: Follow PEP 8, use `black` for formatting
- **Documentation**: Add docstrings for all public methods
- **Type Hints**: Use type annotations where applicable
- **Testing**: Write unit tests for new features

### Areas for Contribution

- 🧠 **New Exploration Strategies**: Implement novel RL exploration methods
- 🎮 **Environment Variations**: Create new maze layouts or robot types
- 📊 **Analysis Tools**: Enhanced visualization and metrics
- 🚀 **Performance Optimization**: Speed up training and simulation
- 📖 **Documentation**: Improve guides and examples

### Reporting Issues

Please use the [GitHub Issues](https://github.com/your-username/q-learning-maze-robot/issues) page to report:

- 🐛 Bugs and errors
- 💡 Feature requests
- 📚 Documentation improvements
- ❓ Questions and support requests

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Thanks to the Godot community for the excellent simulation engine
- Inspired by classic reinforcement learning research
- Built with love for the robotics and AI community

---


