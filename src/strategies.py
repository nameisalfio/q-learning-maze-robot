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
        self.state_visits = {} # Questo è lo stato cruciale da salvare/caricare
    
    def choose_action(self, q_values: np.ndarray, action_counts: np.ndarray = None,
                     state_info: Dict[str, Any] = None) -> int:
        """Choose action based on curiosity and novelty."""
        current_state = state_info.get('current_state') if state_info else None
        
        # Dynamic epsilon based on state novelty
        if current_state is not None:
            visits = self.state_visits.get(current_state, 0)
            self.state_visits[current_state] = visits + 1
            # dynamic_epsilon encourages random exploration more in newer states
            dynamic_epsilon = min(0.8, self.base_epsilon + (0.8 / (visits + 1)))
        else:
            dynamic_epsilon = self.base_epsilon
        
        # Prepare curiosity-adjusted Q-values for exploitation phase
        # This makes the "greedy" choice also sensitive to action novelty
        curiosity_adjusted_q_values = q_values.copy()
        if action_counts is not None:
            # Add novelty bonus: higher for actions tried less often
            # Add a small constant to avoid division by zero if action_count is 0
            novelty_term = self.novelty_bonus / (np.sqrt(action_counts) + 1e-6)
            curiosity_adjusted_q_values += novelty_term

        if random.random() < dynamic_epsilon:
            # Exploration phase:
            # Favor less tried actions even during random exploration
            if action_counts is not None:
                min_count = np.min(action_counts)
                least_tried_actions = np.where(action_counts == min_count)[0]
                return int(np.random.choice(least_tried_actions))
            # Fallback to pure random if action_counts somehow not available
            return random.randint(0, len(q_values) - 1)
        else:
            # Exploitation phase: Use curiosity-adjusted Q-values
            return int(np.argmax(curiosity_adjusted_q_values))
    
    def update(self):
        """Curiosity parameters update dynamically."""
        pass # Nessun decadimento esplicito di base_epsilon qui
    
    @property
    def info(self) -> Dict[str, float]:
        # Questo è ciò che viene salvato attualmente tramite agent.save_model
        return {
            "base_epsilon": self.base_epsilon,
            "novelty_bonus": self.novelty_bonus, # Aggiungiamo anche questo per completezza
            "states_discovered": len(self.state_visits)
        }

    def get_strategy_state(self) -> Dict[str, Any]:
        """Get the internal state of the strategy for saving."""
        return {
            'base_epsilon': self.base_epsilon,
            'novelty_bonus': self.novelty_bonus,
            'state_visits': self.state_visits.copy() # Salva una copia
        }

    def load_strategy_state(self, strategy_state: Dict[str, Any]):
        """Load the internal state of the strategy."""
        self.base_epsilon = strategy_state.get('base_epsilon', self.base_epsilon)
        self.novelty_bonus = strategy_state.get('novelty_bonus', self.novelty_bonus)
        self.state_visits = strategy_state.get('state_visits', {}).copy() # Carica una copia
        self.logger.info(f"CuriosityStrategy state loaded. States discovered: {len(self.state_visits)}")

def create_strategy(config) -> Strategy:
    return CuriosityStrategy(
        base_epsilon=config.get('strategy.epsilon', 0.3),
        novelty_bonus=config.get('strategy.novelty_bonus', 3.0)
    )