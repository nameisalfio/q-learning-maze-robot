import time
import math
from collections import deque
from typing import Tuple, Dict
from dataclasses import dataclass
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from robot.robotic_agent import MoveResult
from lib.dds.dds import DDS

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
    def __init__(self, robot_agent, config):
        self.robot = robot_agent
        self.config = config
        
        # Environment parameters
        self.max_steps = config.get('environment.max_steps', 150)
        self.min_steps = config.get('environment.min_steps', 75) 
        self.collision_limit = config.get('environment.collision_limit', 12)
        self.loop_threshold = config.get('environment.loop_threshold', 18)
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
        
        # Checkpoint tracking
        self.last_checkpoint_step = 0
        self.checkpoint_bonuses = {
            1: 75.0,  
            2: 100.0, 
            3: 125.0, 
            4: 150.0, 
            5: 200.0  # Higher bonus for reaching the final checkpoint
        }
        
        # Enhanced momentum system
        self.momentum_threshold = 3      # Minimum consecutive successful moves to activate momentum bonus
        self.momentum_multiplier = 3.0   # Multiplier for momentum bonus calculation
        self.explosion_threshold = 8     # Threshold for activating explosive bonus for long streaks
    
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
        self.current_position = Position(x, y, theta)
        self.previous_position = self.current_position
        
        return self.get_state()
    
    def reset_checkpoints(self):
        """Reset checkpoint tracking."""
        self.last_checkpoint_step = 0
        self.robot.dds.publish('reset_checkpoints', 1, DDS.DDS_TYPE_INT)
        time.sleep(1.0)
        self.robot.dds.publish('reset_checkpoints', 0, DDS.DDS_TYPE_INT)
        print("Checkpoints reset.")
    
    def get_state(self) -> Tuple[int, int]:
        """Get discretized state representation."""
        x, y, _ = self.robot.get_current_position()
        discrete_x = int(round(x / self.grid_scale))
        discrete_y = int(round(y / self.grid_scale))
        discrete_x = max(-5, min(5, discrete_x))
        discrete_y = max(-5, min(5, discrete_y))
        return (discrete_x, discrete_y)

    def step(self, action: int) -> Tuple[Tuple, float, bool, Dict]:
        """Execute action and return environment response with checkpoint support."""
        self.steps_count += 1
        self.previous_position = self.current_position
        
        action_names = ["UP", "DOWN", "LEFT", "RIGHT"]
        direction = action_names[action]
        
        # Execute robot movement - now returns tuple (result, checkpoint)
        move_result = self.robot.move(direction)
        
        # Handle the new return format
        if isinstance(move_result, tuple):
            result, checkpoint_value = move_result
        else:
            # Backward compatibility
            result = move_result
            checkpoint_value = None
        
        # Update position
        x, y, theta = self.robot.get_current_position()
        self.current_position = Position(x, y, theta)
        self.recent_positions.append(self.current_position)
        
        # Calculate reward with checkpoint support
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
        """Calculate reward with checkpoint bonuses and momentum system."""
        
        # === BASE REWARD ===
        base_rewards = {
            MoveResult.SUCCESS: self.rewards[MoveResult.SUCCESS],
            MoveResult.COLLISION: self.rewards[MoveResult.COLLISION], 
            MoveResult.GOAL_REACHED: self.rewards[MoveResult.GOAL_REACHED],
            MoveResult.TIMEOUT: self.rewards[MoveResult.TIMEOUT],
            MoveResult.CHECKPOINT_REACHED: self.rewards.get(MoveResult.CHECKPOINT_REACHED, 50.0)  # New reward for checkpoint
        }
        
        base_reward = base_rewards.get(result, 0.0)
        total_reward = base_reward
        
        # === CHECKPOINT SYSTEM - VERY HIGH REWARD ===
        if result == MoveResult.CHECKPOINT_REACHED and checkpoint_value is not None:
            # Progressive reward for different checkpoints
            checkpoint_bonus = 75.0 + (checkpoint_value * 25.0)  # Base 75 + 25 for each checkpoint
            total_reward += checkpoint_bonus
            
            # Extra bonus if checkpoint is reached with a long streak
            if self.consecutive_success_moves >= 5:
                total_reward += 50.0
            
            print(f"🎯 CHECKPOINT {checkpoint_value} REACHED! Bonus: {checkpoint_bonus:.1f}, Total reward: {total_reward:.1f}")
        
        # === MOMENTUM SYSTEM - ENCOURAGES CONTINUING IN THE SAME DIRECTION ===
        if result == MoveResult.SUCCESS:
            # Progressive bonus for consecutive movements
            streak_bonus = min(
                self.consecutive_success_moves * self.streak_multiplier * 1.5,  # Increased multiplier
                self.max_streak_bonus * 2  # Doubled max bonus
            )
            total_reward += streak_bonus
            
            # EXTRA MOMENTUM BONUS - Encourages straight movement
            if self.consecutive_success_moves >= 3:
                momentum_bonus = min(self.consecutive_success_moves * 3.0, 30.0)
                total_reward += momentum_bonus
                
            # EXPLOSIVE BONUS for long sequences (straight corridors)
            if self.consecutive_success_moves >= 8:
                explosion_bonus = 25.0 + (self.consecutive_success_moves - 8) * 5.0
                total_reward += explosion_bonus
                print(f"🚀 MOMENTUM BONUS! Streak: {self.consecutive_success_moves}, Extra: {momentum_bonus + explosion_bonus:.1f}")
        
        # === GOAL BONUS WITH CHECKPOINT ===
        elif result == MoveResult.GOAL_REACHED:
            # Extra bonus if goal is reached with a long streak
            streak_bonus = min(self.consecutive_success_moves * 5.0, 100.0)
            total_reward += streak_bonus
            print(f"🏆 GOAL WITH STREAK {self.consecutive_success_moves}! Total: {total_reward:.1f}")
        
        # === PENALTIES FOR UNDESIRED BEHAVIORS ===
        
        # Loop detection penalty (more severe)
        if self._is_in_loop():
            loop_penalty = self.loop_penalty * 1.5  # Increased penalty
            total_reward += loop_penalty
            print(f"🔄 Loop detected! Penalty: {loop_penalty:.1f}")
        
        # Exploration bonus for new states (reduced to favor checkpoints)
        current_state = self.get_state()
        visits = self.visited_states.get(current_state, 0)
        self.visited_states[current_state] = visits + 1
        
        if visits == 0:
            exploration_bonus = self.exploration_bonus * 0.7  # Reduced to favor checkpoints
            total_reward += exploration_bonus
        elif visits > 8:  # Increased penalty for over-visitation
            total_reward -= 4.0
        
        # === ANTI-STAGNATION SYSTEM ===
        # Penalty for lack of progress towards checkpoint/goal
        if result == MoveResult.SUCCESS and self.consecutive_success_moves > 15:
            # Penalize if too many steps are taken without a checkpoint
            if not hasattr(self, 'last_checkpoint_step'):
                self.last_checkpoint_step = 0
            
            steps_since_checkpoint = self.steps_count - self.last_checkpoint_step
            if steps_since_checkpoint > 20:
                stagnation_penalty = -3.0
                total_reward += stagnation_penalty
                print(f"⚠️ Stagnation penalty: {stagnation_penalty:.1f}")
        
        # Update last checkpoint step
        if result == MoveResult.CHECKPOINT_REACHED:
            self.last_checkpoint_step = self.steps_count
        
        if self.steps_count == self.min_steps:
            min_steps_bonus = 15.0
            total_reward += min_steps_bonus
            print(f"🎯 MIN_STEPS BONUS! Reached {self.min_steps} steps, bonus: {min_steps_bonus}")
        
        if self.steps_count > self.min_steps:
            longevity_bonus = 0.5  
            total_reward += longevity_bonus
        
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
        """Controlla se l'episodio deve terminare considerando min_steps."""
        
        # Goal raggiunto - termina sempre (indipendentemente da min_steps)
        if result == MoveResult.GOAL_REACHED:
            return True
        
        # Checkpoint raggiunto - continua sempre (anche oltre max_steps se necessario)
        if result == MoveResult.CHECKPOINT_REACHED:
            return False
        
        # Se non abbiamo raggiunto min_steps, continua (salvo condizioni critiche)
        if self.steps_count < self.min_steps:
            # Termina solo in condizioni critiche anche se sotto min_steps
            if self.collision_count >= self.collision_limit * 1.5:  # Più tollerante
                print(f"⚠️ Critico: Troppe collisioni ({self.collision_count}) prima di min_steps")
                return True
            if self._is_in_loop() and self.steps_count > self.min_steps * 0.8:  # Loop solo verso la fine
                print(f"⚠️ Critico: Loop rilevato vicino alla soglia di min_steps")
                return True
            return False  # Continua l'episodio
        
        # Dopo min_steps, usa le condizioni normali
        if self.steps_count >= self.max_steps:
            print(f"⏱️ Episodio terminato: raggiunto max_steps ({self.max_steps})")
            return True
        if self.collision_count >= self.collision_limit:
            print(f"💥 Episodio terminato: troppe collisioni ({self.collision_count})")
            return True
        if self._is_in_loop() and self.steps_count > self.loop_threshold:
            print(f"🔄 Episodio terminato: loop rilevato dopo {self.steps_count} passi")
            return True
        
        return False