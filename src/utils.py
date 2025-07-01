import yaml
import logging
import os
from datetime import datetime
from typing import Dict, Any

class Config:
    """Configuration manager for the Q-Learning system."""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Config file {self.config_path} not found, using defaults")
            return self._get_defaults()
    
    def _get_defaults(self) -> Dict[str, Any]:
        """Default configuration as fallback."""
        return {
            'agent': {'learning_rate': 0.15, 'discount_factor': 0.98},
            'strategy': {'name': 'curiosity', 'epsilon': 0.7},
            'environment': {'steps': 100},
            'training': {'episodes': 10000, 'model_path': 'models/q_agent.pkl'}
        }
    
    def get(self, key_path: str, default=None):
        """Get configuration value using dot notation (e.g., 'agent.learning_rate')."""
        keys = key_path.split('.')
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

class Logger:
    """Centralized logging system for training and evaluation."""
    
    def __init__(self, name: str = "q_learning", log_level: str = "INFO", session_type: str = "session"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        if not self.logger.handlers:
            self._setup_handlers(session_type)
    
    def _setup_handlers(self, session_type: str):
        """Configure console and file logging handlers."""
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler
        os.makedirs("logs", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_handler = logging.FileHandler(f"logs/{session_type}_{timestamp}.log")
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
    
    def info(self, msg: str):
        """Log info message."""
        self.logger.info(msg)
    
    def warning(self, msg: str):
        """Log warning message."""
        self.logger.warning(msg)
    
    def error(self, msg: str):
        """Log error message."""
        self.logger.error(msg)
    
    def debug(self, msg: str):
        """Log debug message."""
        self.logger.debug(msg)