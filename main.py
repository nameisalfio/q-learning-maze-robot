import sys
import os
sys.path.append('.')

from src.trainer import RLTrainer
from src.utils import Config, Logger
from lib.dds.dds import DDS
from lib.utils.time import Time

def main():
    """Main entry point for Q-Learning Maze Robot system."""
    config = Config()
    logger = Logger(log_level=config.get('experiment.log_level', 'INFO'))
    
    # Initialize robot system
    dds = DDS()
    time_obj = Time()
    
    try:
        trainer = RLTrainer(dds, time_obj)
        
        while True:
            print(f"\n{'='*50}")
            print("Q-LEARNING MAZE ROBOT")
            print(f"Strategy: {config.get('strategy.name', 'unknown')}")
            print(f"{'='*50}")
            print("1. 🎓 Train - Train new agent")
            print("2. 🧪 Test - Test trained agent")
            print("3. 📚 Continue - Continue training")
            print("4. 📊 Stats - Show model statistics")
            print("5. 🚪 Exit - Exit program")
            
            choice = input("\nChoice (1-5): ").strip()
            
            if choice == "1":
                episodes = int(input("Episodes (default from config): ") or config.get('training.episodes', 200))
                trainer.train(n_episodes=episodes)
            elif choice == "2":
                tests = int(input("Test episodes (default from config): ") or config.get('training.test_episodes', 5))
                trainer.test(n_episodes=tests)
            elif choice == "3":
                episodes = int(input("Additional episodes (default 100): ") or "100")
                trainer.train(n_episodes=episodes)
            elif choice == "4":
                trainer.show_stats()
            elif choice == "5":
                print("Goodbye!")
                break
            else:
                print("Invalid option")
    
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            dds.stop()
        except:
            pass

if __name__ == "__main__":
    main()