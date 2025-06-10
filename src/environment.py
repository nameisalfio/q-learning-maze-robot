import time
import math
from collections import deque
from typing import Tuple, Dict
from dataclasses import dataclass
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from robot.robotic_agent import MoveResult

@dataclass
class Position:
    """Robot position representation."""
    x: float
    y: float
    theta: float
    
    def distance_to(self, other: 'Position') -> float:
        """Calculate Euclidean distance to another position."""
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)

class MazeEnvironment:
    """Maze environment for reinforcement learning."""
    
    def __init__(self, robot_agent, config):
        self.robot = robot_agent
        self.config = config
        
        # Environment parameters
        self.max_steps = config.get('environment.max_steps', 100)
        self.collision_limit = config.get('environment.collision_limit', 10)
        self.loop_threshold = config.get('environment.loop_threshold', 15)
        self.grid_scale = config.get('environment.grid_scale', 10)
        
        # Reward configuration
        self.rewards = {
            MoveResult.SUCCESS: config.get('rewards.success', 5.0),
            MoveResult.COLLISION: config.get('rewards.collision', -10.0),
            MoveResult.GOAL_REACHED: config.get('rewards.goal_reached', 100.0),
            MoveResult.TIMEOUT: config.get('rewards.timeout', -5.0),
        }
        
        self.streak_multiplier = config.get('rewards.streak_multiplier', 2.0)
        self.max_streak_bonus = config.get('rewards.max_streak_bonus', 20.0)
        self.exploration_bonus = config.get('rewards.exploration_bonus', 3.0)
        self.loop_penalty = config.get('rewards.loop_penalty', -8.0)
        
        # Environment state
        self.current_position = None
        self.previous_position = None
        self.steps_count = 0
        self.consecutive_success_moves = 0
        self.collision_count = 0
        self.recent_positions = deque(maxlen=6)
        self.visited_states = {}
    
    def reset(self) -> Tuple:
        """Reset environment to initial state."""
        self.steps_count = 0
        self.consecutive_success_moves = 0
        self.collision_count = 0
        self.recent_positions.clear()
        
        # Reset robot to origin
        self.robot.dds.publish('X', 0.0, self.robot.dds.DDS_TYPE_FLOAT)
        self.robot.dds.publish('Y', 0.0, self.robot.dds.DDS_TYPE_FLOAT)
        self.robot.dds.publish('Theta', 0.0, self.robot.dds.DDS_TYPE_FLOAT)
        
        time.sleep(0.5)
        self.robot.dds.wait('tick')
        
        x, y, theta = self.robot.get_current_position()
        self.current_position = Position(x, y, theta)
        self.previous_position = self.current_position
        
        return self.get_state()
    
    def get_state(self) -> Tuple[int, int]:
        """Get discretized state representation."""
        x, y, _ = self.robot.get_current_position()
        discrete_x = int(round(x / self.grid_scale))
        discrete_y = int(round(y / self.grid_scale))
        discrete_x = max(-5, min(5, discrete_x))
        discrete_y = max(-5, min(5, discrete_y))
        return (discrete_x, discrete_y)
    
    def step(self, action: int) -> Tuple[Tuple, float, bool, Dict]:
        """Execute action and return environment response."""
        self.steps_count += 1
        self.previous_position = self.current_position
        
        action_names = ["UP", "DOWN", "LEFT", "RIGHT"]
        direction = action_names[action]
        
        # Execute robot movement
        result = self.robot.move(direction)
        
        # Update position
        x, y, theta = self.robot.get_current_position()
        self.current_position = Position(x, y, theta)
        self.recent_positions.append(self.current_position)
        
        # Calculate reward
        reward = self._calculate_reward(result)
        
        # Update success streak
        if result == MoveResult.SUCCESS:
            self.consecutive_success_moves += 1
        else:
            self.consecutive_success_moves = 0
            if result == MoveResult.COLLISION:
                self.collision_count += 1
        
        # Check termination condition
        done = self._check_done(result)
        
        # Prepare info dictionary
        info = {
            'result': result,
            'steps': self.steps_count,
            'success_streak': self.consecutive_success_moves,
            'total_collisions': self.collision_count,
            'position': (x, y, theta)
        }
        
        return self.get_state(), reward, done, info
    
    def _calculate_reward(self, result: MoveResult) -> float:
        """Calculate reward based on action result and current state."""
        base_reward = self.rewards[result]
        
        if result == MoveResult.SUCCESS:
            # Progressive bonus for consecutive successes
            streak_bonus = min(
                self.consecutive_success_moves * self.streak_multiplier,
                self.max_streak_bonus
            )
            total_reward = base_reward + streak_bonus
        else:
            total_reward = base_reward
            if result == MoveResult.GOAL_REACHED:
                # Extra bonus for reaching goal with long streak
                streak_bonus = min(self.consecutive_success_moves * 3.0, 50.0)
                total_reward += streak_bonus
        
        # Loop detection penalty
        if self._is_in_loop():
            total_reward += self.loop_penalty
        
        # Exploration bonus for new states
        current_state = self.get_state()
        visits = self.visited_states.get(current_state, 0)
        self.visited_states[current_state] = visits + 1
        
        if visits == 0:
            total_reward += self.exploration_bonus
        elif visits > 5:
            total_reward -= 2.0  # Penalty for overvisiting
        
        return total_reward
    
    def _is_in_loop(self) -> bool:
        """Detect if robot is stuck in a movement loop."""
        if len(self.recent_positions) < 4:
            return False
        
        pos_counts = {}
        for pos in self.recent_positions:
            key = (round(pos.x / self.grid_scale), round(pos.y / self.grid_scale))
            pos_counts[key] = pos_counts.get(key, 0) + 1
        
        return max(pos_counts.values()) >= 3
    
    def _check_done(self, result: MoveResult) -> bool:
        """Check if episode should terminate."""
        if result == MoveResult.GOAL_REACHED:
            return True
        if self.steps_count >= self.max_steps:
            return True
        if self.collision_count >= self.collision_limit:
            return True
        if self._is_in_loop() and self.steps_count > self.loop_threshold:
            return True
        return False