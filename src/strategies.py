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
    
'''
class EpsilonGreedyStrategy(Strategy):
    """Classic epsilon-greedy exploration strategy."""
    
    def __init__(self, epsilon: float = 0.8, epsilon_decay: float = 0.995, 
                 epsilon_min: float = 0.1):
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
    
    def choose_action(self, q_values: np.ndarray, action_counts: np.ndarray = None,
                     state_info: Dict[str, Any] = None) -> int:
        """Choose action using epsilon-greedy policy."""
        if random.random() < self.epsilon:
            return random.randint(0, len(q_values) - 1)
        return int(np.argmax(q_values))
    
    def update(self):
        """Decay epsilon parameter."""
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
    
    @property
    def info(self) -> Dict[str, float]:
        return {"epsilon": self.epsilon}

class UCBStrategy(Strategy):
    """Upper Confidence Bound exploration strategy."""
    
    def __init__(self, ucb_factor: float = 2.0, epsilon: float = 0.1):
        self.ucb_factor = ucb_factor
        self.epsilon = epsilon
    
    def choose_action(self, q_values: np.ndarray, action_counts: np.ndarray = None,
                     state_info: Dict[str, Any] = None) -> int:
        """Choose action using UCB policy."""
        if action_counts is None:
            return random.randint(0, len(q_values) - 1)
        
        # Prioritize untried actions
        untried = np.where(action_counts == 0)[0]
        if len(untried) > 0:
            return int(np.random.choice(untried))
        
        # Small random exploration
        if random.random() < self.epsilon:
            return random.randint(0, len(q_values) - 1)
        
        # UCB calculation
        total_visits = np.sum(action_counts)
        ucb_values = q_values + self.ucb_factor * np.sqrt(
            np.log(total_visits + 1) / (action_counts + 1e-6)
        )
        return int(np.argmax(ucb_values))
    
    def update(self):
        """UCB doesn't require parameter updates."""
        pass
    
    @property
    def info(self) -> Dict[str, float]:
        return {"ucb_factor": self.ucb_factor}
'''
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

'''
def create_strategy(config) -> Strategy:
    strategy_name = config.get('strategy.name', 'curiosity')
    
    if strategy_name == 'epsilon_greedy':
        return EpsilonGreedyStrategy(
            epsilon=config.get('strategy.epsilon', 0.8),
            epsilon_decay=config.get('strategy.epsilon_decay', 0.995),
            epsilon_min=config.get('strategy.epsilon_min', 0.1)
        )
    elif strategy_name == 'ucb':
        return UCBStrategy(
            ucb_factor=config.get('strategy.ucb_factor', 2.0),
            epsilon=config.get('strategy.epsilon', 0.1)
        )
    elif strategy_name == 'curiosity':
        return CuriosityStrategy(
            base_epsilon=config.get('strategy.epsilon', 0.3),
            novelty_bonus=config.get('strategy.novelty_bonus', 3.0)
        )
    else:
        raise ValueError(f"Unknown strategy: {strategy_name}")
'''
    
def create_strategy(config) -> Strategy:
    return CuriosityStrategy(
        base_epsilon=config.get('strategy.epsilon', 0.3),
        novelty_bonus=config.get('strategy.novelty_bonus', 3.0)
    )