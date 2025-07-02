import random
import numpy as np
from typing import Dict, Any

class CuriosityStrategy:
    """Curiosity-driven exploration based on state novelty."""
    
    def __init__(self, epsilon: float = 0.3, novelty_bonus: float = 3.0):
        self.epsilon = epsilon
        self.novelty_bonus = novelty_bonus
        self.state_visits = {} # It is crucial to track how many times each state has been visited
    
    def choose_action(self, q_values: np.ndarray, action_counts: np.ndarray = None,
                     state_info: Dict[str, Any] = None) -> int:
        """Choose action based on curiosity and novelty."""
        current_state = state_info.get('current_state') if state_info else None
        
        # Dynamic epsilon based on state novelty
        if current_state is not None:
            visits = self.state_visits.get(current_state, 0)
            self.state_visits[current_state] = visits + 1
            # dynamic_epsilon encourages random exploration more in newer states
            dynamic_epsilon = self.epsilon + (10.0 / (visits + 1))
        else:
            dynamic_epsilon = self.epsilon
        
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
    
    @property
    def info(self) -> Dict[str, float]:
        return {
            "epsilon": self.epsilon,
            "novelty_bonus": self.novelty_bonus,
            "states_discovered": len(self.state_visits)
        }

    def get_strategy_state(self) -> Dict[str, Any]:
        """Get the internal state of the strategy for saving."""
        return {
            'epsilon': self.epsilon,
            'novelty_bonus': self.novelty_bonus,
            'state_visits': self.state_visits.copy()
        }

    def load_strategy_state(self, strategy_state: Dict[str, Any]):
        """Load the internal state of the strategy."""
        self.epsilon = strategy_state.get('epsilon', self.epsilon)
        self.novelty_bonus = strategy_state.get('novelty_bonus', self.novelty_bonus)
        self.state_visits = strategy_state.get('state_visits', {}).copy()
        print(f"CuriosityStrategy state loaded. States discovered: {len(self.state_visits)}")