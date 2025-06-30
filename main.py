import sys
import os
sys.path.append('.')

from src.trainer import RLTrainer
from src.utils import Config, Logger
from lib.dds.dds import DDS
from lib.utils.time import Time
import argparse

def main():
    """Main entry point for Q-Learning Maze Robot system."""
    # --- ARGOMENTI DA RIGA DI COMANDO ---
    parser = argparse.ArgumentParser(description="Q-Learning Maze Robot CLI")
    parser.add_argument(
        "--mode", 
        choices=["train", "test", "continue", "stats", "exit"], 
        help="Operation mode: train, test, continue, stats, exit"
    )
    parser.add_argument(
        "--episodes", 
        type=int, 
        help="Number of episodes for training or continuing"
    )
    parser.add_argument(
        "--test_episodes", 
        type=int, 
        help="Number of episodes for testing"
    )
    # --- NUOVO ARGOMENTO ---
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
            session_type = args.mode # es. 'stats'

    logger = Logger(
        log_level=config.get('experiment.log_level', 'INFO'), 
        session_type=session_type
    )
    
    # Initialize robot system
    dds = DDS()
    time_obj = Time()

    try:
        # --- LOGICA PER DETERMINARE LA MODALITÀ SPOSTATA QUI ---
        fast_mode = False
        if args.fast:
            # Se --fast è specificato, la modalità veloce è sempre attiva.
            fast_mode = True
        elif not args.mode:
            # Se siamo in modalità interattiva (nessun --mode specificato), chiedi all'utente.
            fast_choice = input("Use FAST mode (no physics)? [Y/n]: ").strip().lower()
            fast_mode = fast_choice != 'n'
        # Se siamo in modalità CLI senza --fast, fast_mode rimane False (modalità fisica).

        # --- PASSA IL VALORE FINALE AL TRAINER ---
        trainer = RLTrainer(dds, time_obj, fast_mode=fast_mode)
        
        # --- LOGICA PER GESTIRE MODALITÀ CLI O INTERATTIVA ---
        if args.mode:
            logger.info(f"CLI mode selected: {args.mode}")
            if args.mode == "train":
                num_episodes = args.episodes if args.episodes is not None else config.get('training.episodes', 200)
                logger.info(f"Training for {num_episodes} episodes.")
                trainer.train(n_episodes=num_episodes)
            elif args.mode == "test":
                num_test_episodes = args.test_episodes if args.test_episodes is not None else config.get('training.test_episodes', 5)
                logger.info(f"Testing for {num_test_episodes} episodes.")
                trainer.test(n_episodes=num_test_episodes)
            elif args.mode == "continue":
                num_episodes = args.episodes if args.episodes is not None else 100 # Default per continue
                logger.info(f"Continuing training for {num_episodes} additional episodes.")
                trainer.train(n_episodes=num_episodes)
            elif args.mode == "stats":
                logger.info("Showing model statistics.")
                trainer.show_stats()
            elif args.mode == "exit":
                logger.info("Exiting via CLI command.")
                print("Goodbye!")
        else:
            # Modalità interattiva se non vengono forniti argomenti CLI per la modalità
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
                    tests_input = input(f"Test episodes (default from config: {config.get('training.test_episodes', 5)}): ")
                    tests = int(tests_input) if tests_input else config.get('training.test_episodes', 5)
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