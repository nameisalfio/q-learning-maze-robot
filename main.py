import sys
sys.path.append('.')

from src.trainer import RLTrainer
from src.utils import Config, Logger
from lib.dds.dds import DDS
from lib.utils.time import Time
import argparse

def main():
    parser = argparse.ArgumentParser(description="Q-Learning Maze Robot CLI")
    parser.add_argument(
        "--mode", 
        choices=["train", "test", "continue", "stats", "exit"], 
        help="Operation mode: train, test, continue, stats, exit"
    )
    parser.add_argument(
        "--episodes", 
        type=int, 
        help="Number of episodes"
    )
    parser.add_argument(
        "--fast",
        action='store_true',
        help="Enable fast mode (no physics) for both training and testing."
    )
    
    args = parser.parse_args()

    config = Config()
    session_type = ""
    if args.mode:
        if args.mode in ["train", "continue"]:
            session_type = "training"
        elif args.mode == "test":
            session_type = "testing"
        else:
            session_type = args.mode

    logger = Logger(
        log_level='INFO', 
        session_type=session_type
    )
    
    # Initialize robot system
    dds = DDS()
    time_obj = Time()

    try:
        fast_mode = False
        if args.fast:
            # If --fast is specified, set fast_mode to True.
            fast_mode = True
        elif not args.mode:
            # If we are in interactive mode (no --mode specified), ask the user.
            fast_choice = input("Use FAST mode (no physics)? [Y/n]: ").strip().lower()
            fast_mode = fast_choice != 'n'
        
        # If we are in CLI mode without --fast, fast_mode remains False (physical mode).
        trainer = RLTrainer(dds, time_obj, fast_mode=fast_mode)
        
        if args.mode:
            logger.info(f"CLI mode selected: {args.mode}")
            if args.mode == "train":
                num_episodes = args.episodes if args.episodes is not None else config.get('training.episodes', 200)
                logger.info(f"Training for {num_episodes} episodes.")
                trainer.train(n_episodes=num_episodes)
            elif args.mode == "test":
                num_test_episodes = args.episodes if args.episodes is not None else config.get('test_episodes', 5)
                logger.info(f"Testing for {num_test_episodes} episodes.")
                trainer.test(n_episodes=num_test_episodes)
            elif args.mode == "continue":
                num_episodes = args.episodes if args.episodes is not None else 100 # Default per continue
                logger.info(f"Continuing training for {num_episodes} additional episodes.")
                trainer.train(n_episodes=num_episodes)
            elif args.mode == "stats":
                logger.info("Showing model statistics.")
                trainer.show_stats()
        else:
            # Interactive mode if no CLI arguments are provided for mode
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
                    episodes_input = input(f"Episodes (default from config: {config.get('training.episodes', 200)}): ")
                    episodes = int(episodes_input) if episodes_input else config.get('training.episodes', 200)
                    trainer.train(n_episodes=episodes)
                elif choice == "2":
                    tests_input = input(f"Test episodes (default from config: {config.get('test_episodes', 5)}): ")
                    tests = int(tests_input) if tests_input else config.get('test_episodes', 5)
                    trainer.test(n_episodes=tests)
                elif choice == "3":
                    episodes_input = input("Additional episodes (default 100): ")
                    episodes = int(episodes_input) if episodes_input else 100
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
            logger.info("DDS stopped.")
        except Exception as e:
            logger.error(f"Error stopping DDS: {e}")

if __name__ == "__main__":
    main()