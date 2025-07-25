import time
from collections import deque
from typing import Tuple, Dict
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from robot.robotic_agent import MoveResult
from lib.dds.dds import DDS

class MazeEnvironment:
    def __init__(self, robot_agent, config):
        self.robot = robot_agent
        self.config = config
        
        # Environment parameters
        self.steps = config.get('environment.steps', 200)
        
        # Reward configuration
        self.rewards = {
            MoveResult.COLLISION: config.get('rewards.collision', -13.0),
            MoveResult.GOAL_REACHED: config.get('rewards.goal_reached', 1000.0),
        }
        
        self.loop_penalty = config.get('rewards.loop_penalty', -13.0)
        
        # Environment state
        self.current_position = None
        self.steps_count = 0
        self.consecutive_success_moves = 0
        self.collision_count = 0
        self.recent_positions = deque(maxlen=6)
        
        # Checkpoint tracking
        self.checkpoint_bonuses = {
            1: 50.0,  
            2: 150.0, 
            3: 300.0,
            4: 500.0
        }
    
    def reset(self) -> Tuple:
        """Reset environment to initial state."""
        self.steps_count = 0
        self.consecutive_success_moves = 0
        self.collision_count = 0
        self.recent_positions.clear()
        # Reset robot
        self.robot.reset()
        
        time.sleep(0.5)
        x, y, theta = self.robot.get_current_position()
        self.current_position = (x,y, theta)
        
        return self.get_state()
    
    def reset_checkpoints(self):
        """Reset checkpoint tracking."""
        self.robot.dds.publish('reset_checkpoints', 1, DDS.DDS_TYPE_INT)
        time.sleep(1.0)
        self.robot.dds.publish('reset_checkpoints', 0, DDS.DDS_TYPE_INT)
        print("Checkpoints reset.")

    def get_state(self) -> Tuple[float, float]:
        """
        Get the discretized robot's (x,y) state representation.
        This is crucial for bridging the gap between continuous real-mode
        physics and discrete fast-mode training.
        """
        x, y, _ = self.robot.get_current_position()
        discretized_x = round(x, 1)
        discretized_y = round(y, 1)
        
        return discretized_x, discretized_y

    def step(self, action: int) -> Tuple[Tuple, float, bool, Dict]:
        """Execute action and return the environment's response."""
        self.steps_count += 1
        
        action_names = ["UP", "DOWN", "LEFT", "RIGHT"]
        direction = action_names[action]
        
        # Execute robot movement - returns tuple (result, checkpoint_value) if checkpoint is reached
        # or just result if no checkpoint is reached
        move_result = self.robot.move(direction)
        
        # Handle the result
        if isinstance(move_result, tuple):
            result, checkpoint_value = move_result
        else:
            result = move_result
            checkpoint_value = None
        
        # Update position
        x, y, theta = self.robot.get_current_position()
        self.current_position = (x, y, theta)
        self.recent_positions.append(self.current_position)

        # Calculate reward
        reward = self._calculate_reward(result, checkpoint_value)

        # Update success streak
        if result == MoveResult.SUCCESS or result == MoveResult.CHECKPOINT_REACHED:
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
            'checkpoint': checkpoint_value,
            'steps': self.steps_count,
            'success_streak': self.consecutive_success_moves,
            'total_collisions': self.collision_count,
            'position': (x, y, theta)
        }
        
        return self.get_state(), reward, done, info

    def _calculate_reward(self, result: MoveResult, checkpoint_value=None) -> float:
        """Calculate rewards."""
        
        total_reward = 0

        # === BASE REWARD ===
        base_rewards = {
            MoveResult.COLLISION: self.rewards[MoveResult.COLLISION], 
            MoveResult.GOAL_REACHED: self.rewards[MoveResult.GOAL_REACHED],
        }
        
        total_reward += base_rewards.get(result, 0.0)
        
        # checkpoint reward
        if result == MoveResult.CHECKPOINT_REACHED and checkpoint_value is not None:
            checkpoint_bonus = self.checkpoint_bonuses[checkpoint_value]
            total_reward += checkpoint_bonus
            print(f"🎯 CHECKPOINT {checkpoint_value} REACHED! Bonus: {checkpoint_bonus:.1f}, Total reward: {total_reward:.1f}")
        
        # Streak bonus if goal is reached
        if result == MoveResult.GOAL_REACHED:
            # Extra bonus if goal is reached with a long streak
            streak_bonus = self.consecutive_success_moves * 20.0
            total_reward += streak_bonus
                
        # Loop detection penalty
        if self._is_in_loop():
            loop_penalty = self.loop_penalty * 1.5  # Increased penalty
            total_reward += loop_penalty
            print(f"🔄 Loop detected! Penalty: {loop_penalty:.1f}")
        
        return total_reward

    def _is_in_loop(self) -> bool:
        """Detect if robot is stuck in a movement loop."""
        if len(self.recent_positions) < 4:
            return False
        
        pos_counts = {}
        for pos in self.recent_positions:
            key = (pos[0], pos[1])
            pos_counts[key] = pos_counts.get(key, 0) + 1
        
        return max(pos_counts.values()) >= 3
    
    def _check_done(self, result: MoveResult) -> bool:
        """Check if the episode is done."""

        # Goal reached
        if result == MoveResult.GOAL_REACHED:
            return True

        # Check if we have reached the end of the available steps
        if self.steps_count >= self.steps:
            print(f"⏱️ Episode ended: reached maximum steps ({self.steps})")
            return True
        
        return False