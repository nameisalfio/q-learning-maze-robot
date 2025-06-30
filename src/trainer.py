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
    """Main trainer for Q-Learning maze navigation with enhanced episode formatting."""
    
    def __init__(self, dds, time_obj, fast_mode: bool, config_path: str = "config.yaml"):
        """Initialize the RL trainer with all necessary components."""
        self.dds = dds
        self.time = time_obj
        self.config = Config(config_path)
        self.logger = Logger(log_level=self.config.get('experiment.log_level', 'INFO'))
        
        self.fast_mode = fast_mode
        self.logger.info(f"Movement Mode: {'FAST (Teleport)' if self.fast_mode else 'REAL (Physics)'}")

        # Initialize system components
        self.robot = DiffDriveRoboticAgent(dds, time_obj, fast_mode=self.fast_mode)
        self.environment = MazeEnvironment(self.robot, self.config)
        
        # Create strategy
        strategy = create_strategy(self.config)
        self.agent = QLearningAgent(self.config, strategy)
        
        self.model_path = str(self.config.get('training.model_path', 'models/q_agent.pkl'))
        
        # Verification logging
        self.logger.info(f"Strategy initialized: {type(strategy).__name__}")
        self.logger.info(f"Strategy info: {strategy.info}")
    
    def train(self, n_episodes: int = None, save_every: int = None):
        """Train the Q-Learning agent with enhanced episode formatting."""
        n_episodes = n_episodes or self.config.get('training.episodes', 200)
        save_every = save_every or self.config.get('training.save_every', 50)
        
        # Get environment parameters for display
        
        self.logger.info("=" * 80)
        self.logger.info("🚀 STARTING TRAINING SESSION")
        self.logger.info("=" * 80)
        self.logger.info(f"Episodes: {n_episodes}")
        self.logger.info(f"Strategy: {self.config.get('strategy.name', 'unknown')}")
        self.logger.info(f"Model path: {self.model_path}")
        self.logger.info("=" * 80)
        
        # Load existing model if available
        if self.agent.load_model(self.model_path):
            self.logger.info("📁 Loaded existing model")
        
        self.dds.wait('tick')
        self.logger.info("🔗 Connected to Godot simulation!")
        
        # Training statistics
        checkpoint_stats = {
            'total_checkpoints': 0,
            'unique_checkpoints': set(),
            'checkpoint_episodes': 0,
        }
        
        try:
            # RIMOSSO: self.robot.set_train_mode()
            for episode in range(n_episodes):
                self._print_episode_header(episode + 1, n_episodes)
                
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
                
                # Episode completed statistics
                steps_taken = info['steps']
                self.agent.episode_rewards.append(total_reward)
                self.agent.episode_steps.append(steps_taken)
                success = (info['result'] == MoveResult.GOAL_REACHED)
                self.agent.success_episodes.append(success)
                
                # Track checkpoint episodes
                if episode_checkpoints:
                    checkpoint_stats['checkpoint_episodes'] += 1

                self.environment.reset_checkpoints()
                
                # Update exploration strategy
                self.agent.update_strategy()

                # update learning rate
                self.agent.update_learning_rate()
                
                # Enhanced episode summary
                self._print_episode_summary(episode + 1, info, total_reward, max_streak, 
                                          episode_checkpoints)
                
                # Periodic model saving and stats
                if (episode + 1) % save_every == 0:
                    model_path_with_number = self.model_path.split(".")[0] + f"_{episode+1}." + self.model_path.split(".")[1]
                    self.agent.save_model(model_path_with_number)
                    self.agent.save_model(self.model_path)
                    self._print_stats_with_checkpoints(checkpoint_stats, episode + 1)
                    
        except KeyboardInterrupt:
            self.logger.info("⚠️ Training interrupted by user")
        finally:
            self.agent.save_model(self.model_path)
            self.logger.info("✅ Training completed!")
            self._print_final_stats_with_checkpoints(checkpoint_stats)
    
    def test(self, n_episodes: int = None):
        """Test the trained agent with strategy display."""
        n_episodes = n_episodes or self.config.get('training.test_episodes', 5)
        
        print("\n" + "=" * 80)
        print("🧪 TESTING MODE")
        print("=" * 80)
        
        if not self.agent.load_model(self.model_path):
            self.logger.error("❌ No trained model found!")
            return
        
        # Display strategy info
        strategy_info = self.agent.strategy.info if hasattr(self.agent.strategy, 'info') else {}
        strategy_name = strategy_info.get('strategy', type(self.agent.strategy).__name__)
        print(f"🎯 Testing Strategy: {strategy_name.upper()}")
        print(f"📊 Strategy Details: {strategy_info}")
        print("=" * 80)
        
        self.dds.wait('tick')
        
        successes = 0
        total_steps = 0
        
        try:
            for episode in range(n_episodes):                
                print(f"\n🧪 TEST EPISODE {episode + 1}/{n_episodes}")
                print("-" * 50)
                
                state = self.environment.reset()
                self.environment.reset_checkpoints()
                done = False
                step_count = 0
                
                while not done:
                    # Use greedy policy (no exploration)
                    action = self.agent.choose_action(state, training=False)
                    state, reward, done, info = self.environment.step(action)
                    step_count += 1
                    
                    # Show progress every 20 steps
                    if step_count % 20 == 0:
                        print(f"   Step {step_count}: Position {info['position'][:2]}")
                
                total_steps += info['steps']
                
                if info['result'] == MoveResult.GOAL_REACHED:
                    successes += 1
                    print(f"✅ Goal reached in {info['steps']} steps!")
                else:
                    print(f"⚠️ Test incomplete: {info['result'].value}")
            
        finally:
            print(f"\n📊 TEST RESULTS:")
            print("=" * 50)
            self.logger.info(f"Success rate: {successes}/{n_episodes} ({successes/n_episodes:.1%})")
            self.logger.info(f"Average steps: {total_steps/n_episodes:.1f}")
            print("=" * 50)
    
    def show_stats(self):
        """Display model statistics."""
        if self.agent.load_model(self.model_path):
            stats = self.agent.get_stats()
            self.logger.info("Model Statistics:")
            for key, value in stats.items():
                self.logger.info(f"  {key}: {value}")
        else:
            self.logger.error("No trained model found!")
    
    def _print_episode_header(self, episode_num: int, total_episodes: int):
        """Print formatted episode header with strategy information."""
        
        # Get current strategy info
        strategy_info = self.agent.strategy.info if hasattr(self.agent.strategy, 'info') else {}
        strategy_name = strategy_info.get('strategy', type(self.agent.strategy).__name__)
        
        # Create header
        header_line = "=" * 100
        print(f"\n{header_line}")
        print(f"🎯 EPISODE {episode_num:3d}/{total_episodes} | Strategy: {strategy_name.upper()}")
        print(f"{header_line}")
        
        # Strategy-specific details
        if strategy_name == 'curiosity':
            states_discovered = strategy_info.get('states_discovered', 0)
            base_epsilon = strategy_info.get('epsilon', 0.7)
            print(f"🧠 Curiosity Details: Base ε={base_epsilon:.3f} | States Discovered: {states_discovered}")
        
        # Episode requirements
        print(f"🎮 Starting position: (0.0, 0.0)")
        print(f"{'-' * 100}")
        
        # Log to file as well
        self.logger.info(f"Episode {episode_num}/{total_episodes} started - Strategy: {strategy_name}")
    
    def _print_episode_summary(self, episode_num: int, info: dict, total_reward: float,
                             max_streak: int, episode_checkpoints: list):
        """Print comprehensive episode summary."""
        
        steps_taken = info['steps']
        result = info['result']
        
        # Choose symbol based on result
        if result == MoveResult.GOAL_REACHED:
            symbol = "🏆"
            status = "GOAL REACHED"
        else:
            if episode_checkpoints:
                symbol = "🔶"
                status = "CHECKPOINTS (Short)"
            else:
                symbol = "❌"
                status = "FAILED (Short)"
        
        # Episode summary line
        summary_line = "-" * 100
        print(f"{summary_line}")
        print(f"{symbol} EPISODE {episode_num} COMPLETED | Status: {status}")
        print(f"📊 Reward: {total_reward:6.1f} | Steps: {steps_taken:3d} | Max Streak: {max_streak}")
        
        # Checkpoint info
        if episode_checkpoints:
            unique_checkpoints = len(set(episode_checkpoints))
            print(f"📍 Checkpoints: {episode_checkpoints} (unique: {unique_checkpoints})")
        
        # Performance indicators
        performance_indicators = []
        if episode_checkpoints:
            performance_indicators.append(f"📍 {len(set(episode_checkpoints))} Checkpoints")
        if max_streak >= 30:
            performance_indicators.append(f"🔥 {max_streak} Streak")
        if info['total_collisions'] <= 40:
            performance_indicators.append("🛡️ Low Collisions")
        
        if performance_indicators:
            print(f"🎯 Performance: {' | '.join(performance_indicators)}")
        
        print(f"{summary_line}\n")
        
        # Log summary to file
        self.logger.info(f"{symbol} Episode {episode_num}: {status} | "
                        f"Reward: {total_reward:.1f} | Steps: {steps_taken}")
    
    def _print_stats_with_checkpoints(self, checkpoint_stats: dict, episodes_completed: int):
        """Print training statistics including checkpoint information."""
        if not self.agent.episode_rewards:
            return
        
        recent_rewards = self.agent.episode_rewards[-50:]
        recent_steps = self.agent.episode_steps[-50:]
        recent_success = self.agent.success_episodes[-50:]
        
        print("\n" + "=" * 80)
        print("📊 TRAINING STATISTICS")
        print("=" * 80)
        self.logger.info(f"Episodes completed: {episodes_completed}")
        self.logger.info(f"Average reward (last 50): {np.mean(recent_rewards):.2f}")
        self.logger.info(f"Average steps (last 50): {np.mean(recent_steps):.1f}")
        self.logger.info(f"Success rate (last 50): {sum(recent_success)/len(recent_success):.1%}")
        self.logger.info(f"States explored: {len(self.agent.q_table)}")
        
        # Checkpoint statistics
        print("\n📍 CHECKPOINT STATISTICS")
        print("-" * 40)
        self.logger.info(f"Total checkpoints reached: {checkpoint_stats['total_checkpoints']}")
        self.logger.info(f"Unique checkpoints discovered: {len(checkpoint_stats['unique_checkpoints'])}")
        self.logger.info(f"Episodes with checkpoints: {checkpoint_stats['checkpoint_episodes']}/{episodes_completed}")
        
        if checkpoint_stats['unique_checkpoints']:
            self.logger.info(f"Checkpoint values found: {sorted(checkpoint_stats['unique_checkpoints'])}")
        
        print("=" * 80 + "\n")
    
    def _print_final_stats_with_checkpoints(self, checkpoint_stats: dict):
        """Print final training statistics with checkpoint analysis."""
        stats = self.agent.get_stats()
        if stats:
            self.logger.info("=== FINAL TRAINING STATISTICS ===")
            for key, value in stats.items():
                self.logger.info(f"  {key}: {value}")
            
            # Final checkpoint analysis
            self.logger.info("=== FINAL CHECKPOINT ANALYSIS ===")
            total_episodes = len(self.agent.episode_rewards)
            if total_episodes > 0:
                checkpoint_discovery_rate = len(checkpoint_stats['unique_checkpoints']) / total_episodes
                checkpoint_frequency = checkpoint_stats['total_checkpoints'] / total_episodes
                
                self.logger.info(f"  Checkpoint discovery rate: {checkpoint_discovery_rate:.3f} unique/episode")
                self.logger.info(f"  Checkpoint frequency: {checkpoint_frequency:.3f} checkpoints/episode")
                
                if checkpoint_stats['unique_checkpoints']:
                    best_checkpoint = max(checkpoint_stats['unique_checkpoints'])
                    progress_percentage = len(checkpoint_stats['unique_checkpoints']) / 5 * 100  # Assuming 5 total checkpoints
                    self.logger.info(f"  Best checkpoint reached: {best_checkpoint}")
                    self.logger.info(f"  Maze progress: {progress_percentage:.1f}% (checkpoints discovered)")