import numpy as np
import pickle
import os
from typing import Tuple, Dict
from .strategies import CuriosityStrategy

class QLearningAgent:
    """Q-Learning agent for maze navigation."""
    
    def __init__(self, config):
        # Q-Learning parameters
        self.learning_rate = config.get('agent.learning_rate', 0.1)
        self.discount_factor = config.get('agent.discount_factor', 0.95)
        self.min_lr = config.get('agent.min_learning_rate', 0.01)
        self.lr_decay = config.get('agent.lr_decay', 0.995)
        
        # La strategia viene creata direttamente qui
        self.strategy = CuriosityStrategy(
            epsilon=config.get('strategy.epsilon', 0.3),
            novelty_bonus=config.get('strategy.novelty_bonus', 3.0)
        )
        
        # Q-table and action tracking
        self.q_table = {}
        self.action_counts = {}
        self.n_actions = 4
        
        # Training statistics
        self.episode_rewards = []
        self.episode_steps = []
        self.success_episodes = []
    
    def get_q_values(self, state: Tuple) -> np.ndarray:
        """Get Q-values for a given state."""
        if state not in self.q_table:
            self.q_table[state] = np.random.uniform(0.1, 1.0, self.n_actions)
            self.action_counts[state] = np.zeros(self.n_actions)
        return self.q_table[state]
    
    def choose_action(self, state: Tuple, training: bool = True) -> int:
        """Choose action using the current strategy."""
        q_values = self.get_q_values(state)
        
        if not training:
            # Greedy action for testing
            return int(np.argmax(q_values))
        
        action_counts = self.action_counts[state]
        state_info = {'current_state': state}
        
        action = self.strategy.choose_action(q_values, action_counts, state_info)
        self.action_counts[state][action] += 1
        return action
    
    def update_learning_rate(self):
        self.learning_rate = max(self.min_lr, self.learning_rate * self.lr_decay)

    def update_q_value(self, state: Tuple, action: int, reward: float,
                      next_state: Tuple, done: bool = False):
        """Update Q-value using Q-Learning rule."""
        current_q = self.get_q_values(state)[action]
        
        if done:
            target = reward
        else:
            next_q_values = self.get_q_values(next_state)
            target = reward + self.discount_factor * np.max(next_q_values)
        
        self.q_table[state][action] += self.learning_rate * (target - current_q)
    
    def save_model(self, filepath: str):
        """Save the trained model to file."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        model_data = {
            'q_table': self.q_table,
            'action_counts': self.action_counts,
            'episode_rewards': self.episode_rewards,
            'episode_steps': self.episode_steps,
            'success_episodes': self.success_episodes,
            'strategy_state': self.strategy.get_strategy_state() if hasattr(self.strategy, 'get_strategy_state') else self.strategy.info
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)

    def load_model(self, filepath: str) -> bool:
        """Load a trained model from file."""
        if not os.path.exists(filepath):
            return False
        
        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
            
            self.q_table = model_data['q_table']
            self.action_counts = model_data.get('action_counts', {})
            self.episode_rewards = model_data.get('episode_rewards', [])
            self.episode_steps = model_data.get('episode_steps', [])
            self.success_episodes = model_data.get('success_episodes', [])

            saved_strategy_state = model_data.get('strategy_state')
            if saved_strategy_state and hasattr(self.strategy, 'load_strategy_state'):
                self.strategy.load_strategy_state(saved_strategy_state)

            for state in self.q_table:
                if state not in self.action_counts:
                    self.action_counts[state] = np.zeros(self.n_actions)
            
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """Get comprehensive agent statistics."""
        if not self.episode_rewards:
            return {}
        
        return {
            'total_episodes': len(self.episode_rewards),
            'states_explored': len(self.q_table),
            'avg_reward': np.mean(self.episode_rewards),
            'max_reward': np.max(self.episode_rewards),
            'success_rate': sum(self.success_episodes) / len(self.success_episodes),
            'strategy_info': self.strategy.info
        }