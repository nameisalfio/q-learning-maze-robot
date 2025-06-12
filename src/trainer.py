import numpy as np
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from robot.robotic_agent import DiffDriveRoboticAgent, MoveResult
from .agent import QLearningAgent
from .environment import MazeEnvironment
from .strategies import create_strategy
from .utils import Config, Logger

class RLTrainer:
    """Main trainer for Q-Learning maze navigation."""
    
    def __init__(self, dds, time_obj, config_path: str = "config.yaml"):
        self.dds = dds
        self.time = time_obj
        self.config = Config(config_path)
        self.logger = Logger(log_level=self.config.get('experiment.log_level', 'INFO'))
        
        # Initialize system components
        self.robot = DiffDriveRoboticAgent(dds, time_obj)
        self.environment = MazeEnvironment(self.robot, self.config)
        
        strategy = create_strategy(self.config)
        self.agent = QLearningAgent(self.config, strategy)
        
        self.model_path = self.config.get('training.model_path', 'models/q_agent.pkl')
    
    def train(self, n_episodes: int = None, save_every: int = None):
        """Train the Q-Learning agent with checkpoint tracking."""
        n_episodes = n_episodes or self.config.get('training.episodes', 200)
        save_every = save_every or self.config.get('training.save_every', 50)
        
        self.logger.info(f"Starting training for {n_episodes} episodes")
        self.logger.info(f"Strategy: {self.config.get('strategy.name', 'unknown')}")
        
        # Load existing model if available
        if self.agent.load_model(self.model_path):
            self.logger.info("Loaded existing model")
        
        self.dds.wait('tick')
        self.logger.info("Connected to Godot simulation!")
        
        # Tracking checkpoint statistics
        checkpoint_stats = {
            'total_checkpoints': 0,
            'unique_checkpoints': set(),
            'checkpoint_episodes': 0
        }
        
        try:
            for episode in range(n_episodes):
                self.logger.info(f"Episode {episode + 1}/{n_episodes}")
                
                # Reset environment for new episode
                state = self.environment.reset()
                total_reward = 0
                done = False
                max_streak = 0
                episode_checkpoints = []
                
                # Episode loop
                while not done:
                    action = self.agent.choose_action(state, training=True)
                    next_state, reward, done, info = self.environment.step(action)
                    
                    # Track checkpoints in this episode
                    if info.get('checkpoint') is not None:
                        checkpoint_value = info['checkpoint']
                        episode_checkpoints.append(checkpoint_value)
                        checkpoint_stats['total_checkpoints'] += 1
                        checkpoint_stats['unique_checkpoints'].add(checkpoint_value)
                    
                    # Update Q-table
                    self.agent.update_q_value(state, action, reward, next_state, done)
                    
                    total_reward += reward
                    state = next_state
                    max_streak = max(max_streak, info['success_streak'])
                
                # Episode completed - record statistics
                self.agent.episode_rewards.append(total_reward)
                self.agent.episode_steps.append(info['steps'])
                success = (info['result'] == MoveResult.GOAL_REACHED)
                self.agent.success_episodes.append(success)
                
                # Reset environment checkpoints for next episode
                self.environment.reset_checkpoints()

                # Track checkpoint episodes
                if episode_checkpoints:
                    checkpoint_stats['checkpoint_episodes'] += 1
                
                # Update exploration strategy
                self.agent.update_strategy()
                
                # Enhanced episode logging with checkpoint info
                symbol = "🎯" if success else "📍" if episode_checkpoints else "💥" if info['total_collisions'] > 0 else "⏱️"
                strategy_info = self.agent.strategy.info
                
                checkpoint_info = ""
                if episode_checkpoints:
                    unique_checkpoints = len(set(episode_checkpoints))
                    checkpoint_info = f", Checkpoints: {episode_checkpoints} (unique: {unique_checkpoints})"
                
                self.logger.info(f"{symbol} Episode {episode + 1}: "
                            f"Reward: {total_reward:.1f}, Steps: {info['steps']}, "
                            f"Max streak: {max_streak}{checkpoint_info}")
                
                # Strategy info
                self.logger.info(f"   Strategy: {strategy_info}")
                
                # Calculate recent success rate
                if len(self.agent.success_episodes) >= 20:
                    recent_success = sum(self.agent.success_episodes[-20:]) / 20
                    recent_checkpoints = sum(1 for i in range(max(0, episode-19), episode+1) 
                                        if i < len(self.agent.episode_rewards))
                    self.logger.info(f"   Success rate (last 20): {recent_success:.1%}, "
                                f"Checkpoint episodes: {recent_checkpoints}/20")
                
                # Periodic model saving and enhanced stats
                if (episode + 1) % save_every == 0:
                    self.agent.save_model(self.model_path)
                    self._print_stats(checkpoint_stats, episode + 1)
                    
        except KeyboardInterrupt:
            self.logger.info("Training interrupted by user")
        finally:
            self.agent.save_model(self.model_path)
            self.logger.info("Training completed!")
            self._print_final_stats(checkpoint_stats) 

    def test(self, n_episodes: int = None):
        """Test the trained agent."""
        n_episodes = n_episodes or self.config.get('training.test_episodes', 5)
        
        self.logger.info(f"Testing agent for {n_episodes} episodes")
        
        if not self.agent.load_model(self.model_path):
            self.logger.error("No trained model found!")
            return
        
        self.dds.wait('tick')
        
        successes = 0
        total_steps = 0
        
        try:
            for episode in range(n_episodes):
                self.logger.info(f"Test episode {episode + 1}/{n_episodes}")
                
                state = self.environment.reset()
                done = False
                
                while not done:
                    # Use greedy policy (no exploration)
                    action = self.agent.choose_action(state, training=False)
                    state, reward, done, info = self.environment.step(action)
                
                total_steps += info['steps']
                
                if info['result'] == MoveResult.GOAL_REACHED:
                    successes += 1
                    self.logger.info(f"Goal reached in {info['steps']} steps!")
                else:
                    self.logger.info(f"Test failed: {info['result'].value}")
        
        finally:
            self.logger.info("Test Results:")
            self.logger.info(f"Success rate: {successes}/{n_episodes} ({successes/n_episodes:.1%})")
            self.logger.info(f"Average steps: {total_steps/n_episodes:.1f}")

    def show_stats(self):
        """Display model statistics."""
        if self.agent.load_model(self.model_path):
            stats = self.agent.get_stats()
            self.logger.info("Model Statistics:")
            for key, value in stats.items():
                self.logger.info(f"  {key}: {value}")
        else:
            self.logger.error("No trained model found!")

    def _print_stats(self, checkpoint_stats: dict, episodes_completed: int):
        """Print training statistics including checkpoint information."""
        if not self.agent.episode_rewards:
            return
        
        recent_rewards = self.agent.episode_rewards[-50:]
        recent_steps = self.agent.episode_steps[-50:]
        recent_success = self.agent.success_episodes[-50:]
        
        self.logger.info("=== TRAINING STATISTICS ===")
        self.logger.info(f"Episodes completed: {episodes_completed}")
        self.logger.info(f"Average reward (last 50): {np.mean(recent_rewards):.2f}")
        self.logger.info(f"Average steps (last 50): {np.mean(recent_steps):.1f}")
        self.logger.info(f"Success rate (last 50): {sum(recent_success)/len(recent_success):.1%}")
        self.logger.info(f"States explored: {len(self.agent.q_table)}")
        
        # Checkpoint statistics
        self.logger.info("=== CHECKPOINT STATISTICS ===")
        self.logger.info(f"Total checkpoints reached: {checkpoint_stats['total_checkpoints']}")
        self.logger.info(f"Unique checkpoints discovered: {len(checkpoint_stats['unique_checkpoints'])}")
        self.logger.info(f"Episodes with checkpoints: {checkpoint_stats['checkpoint_episodes']}/{episodes_completed}")
        if checkpoint_stats['unique_checkpoints']:
            self.logger.info(f"Checkpoint values found: {sorted(checkpoint_stats['unique_checkpoints'])}")

    def _print_final_stats(self, checkpoint_stats: dict):
        """Print final training statistics with checkpoint analysis."""
        stats = self.agent.get_stats()
        if stats:
            self.logger.info("=== FINAL TRAINING STATISTICS ===")
            for key, value in stats.items():
                self.logger.info(f"  {key}: {value}")
            
            # Final checkpoint analysis
            self.logger.info("=== FINAL CHECKPOINT ANALYSIS ===")
            total_episodes = len(self.agent.episode_rewards)
            checkpoint_discovery_rate = len(checkpoint_stats['unique_checkpoints']) / max(1, total_episodes)
            checkpoint_frequency = checkpoint_stats['total_checkpoints'] / max(1, total_episodes)
            
            self.logger.info(f"  Checkpoint discovery rate: {checkpoint_discovery_rate:.3f} unique/episode")
            self.logger.info(f"  Checkpoint frequency: {checkpoint_frequency:.3f} checkpoints/episode")
            self.logger.info(f"  Best checkpoint reached: {max(checkpoint_stats['unique_checkpoints']) if checkpoint_stats['unique_checkpoints'] else 'None'}")
            
            if checkpoint_stats['unique_checkpoints']:
                progress_percentage = len(checkpoint_stats['unique_checkpoints']) / 5 * 100  # Assuming 5 total checkpoints
                self.logger.info(f"  Maze progress: {progress_percentage:.1f}% (checkpoints discovered)")