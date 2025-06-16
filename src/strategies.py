import random
import numpy as np
import math
from abc import ABC, abstractmethod
from typing import Dict, Any

class Strategy(ABC):
    """Abstract base class for exploration strategies."""
    
    @abstractmethod
    def choose_action(self, q_values: np.ndarray, action_counts: np.ndarray = None, 
                     state_info: Dict[str, Any] = None) -> int:
        """Choose an action based on the strategy."""
        pass
    
    @abstractmethod
    def update(self):
        """Update strategy parameters (e.g., epsilon decay)."""
        pass
    
    @property
    @abstractmethod
    def info(self) -> Dict[str, float]:
        """Return current strategy parameters."""
        pass
    
class CuriosityStrategy(Strategy):
    """Curiosity-driven exploration based on state novelty."""
    
    def __init__(self, base_epsilon: float = 0.3, novelty_bonus: float = 3.0):
        self.base_epsilon = base_epsilon
        self.novelty_bonus = novelty_bonus
        self.state_visits = {}
    
    def choose_action(self, q_values: np.ndarray, action_counts: np.ndarray = None,
                     state_info: Dict[str, Any] = None) -> int:
        """Choose action based on curiosity and novelty."""
        current_state = state_info.get('current_state') if state_info else None
        
        # Dynamic epsilon based on state novelty
        if current_state is not None:
            visits = self.state_visits.get(current_state, 0)
            self.state_visits[current_state] = visits + 1
            dynamic_epsilon = min(0.8, self.base_epsilon + (0.5 / (visits + 1)))
        else:
            dynamic_epsilon = self.base_epsilon
        
        if random.random() < dynamic_epsilon:
            # Favor less tried actions
            if action_counts is not None:
                min_count = np.min(action_counts)
                least_tried = np.where(action_counts == min_count)[0]
                return int(np.random.choice(least_tried))
            return random.randint(0, len(q_values) - 1)
        
        return int(np.argmax(q_values))
    
    def update(self):
        """Curiosity parameters update dynamically."""
        pass
    
    @property
    def info(self) -> Dict[str, float]:
        return {
            "base_epsilon": self.base_epsilon,
            "states_discovered": len(self.state_visits)
        }
    
def create_strategy(config) -> Strategy:
    return CuriosityStrategy(
        base_epsilon=config.get('strategy.epsilon', 0.3),
        novelty_bonus=config.get('strategy.novelty_bonus', 3.0)
    )