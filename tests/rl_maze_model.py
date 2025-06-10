import sys
sys.path.append("../")

import numpy as np
import random
import pickle
import os
import math
import time
from collections import deque
from typing import Tuple, Dict
from dataclasses import dataclass
from RoboticAgent import DiffDriveRoboticAgent, MoveResult, DIRECTIONS
from lib.dds.dds import DDS
from lib.utils.time import Time


@dataclass
class Position:
    """Rappresentazione semplice di una posizione"""
    x: float
    y: float
    theta: float
    
    def distance_to(self, other: 'Position') -> float:
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)


class SimpleMazeEnvironment:
    """Ambiente del labirinto semplificato con sistema di ricompense progressive"""
    
    def __init__(self, robot_agent):
        self.robot = robot_agent
        self.current_position = None
        self.previous_position = None
        
        # Contatori
        self.steps_count = 0
        self.max_steps = 150
        self.consecutive_success_moves = 0  # Contatore per movimenti consecutivi di successo
        self.collision_count = 0
        
        # Sistema di ricompense progressive
        self.base_rewards = {
            MoveResult.SUCCESS: 2.0,           # Ricompensa base aumentata per movimento riuscito
            MoveResult.COLLISION: -3.0,        # Penalità per collisione
            MoveResult.GOAL_REACHED: 100.0,    # Ricompensa finale per goal
            MoveResult.TIMEOUT: -10.0,         # Penalità per timeout
        }
        
        # Bonus progressivi per movimenti consecutivi senza collisioni
        self.success_streak_bonus = 1.0      # Bonus per ogni movimento consecutivo
        self.max_streak_bonus = 15.0         # Massimo bonus accumulabile
        
        # Rilevamento loop semplificato
        self.recent_positions = deque(maxlen=8)
        
    def reset(self) -> Tuple:
        """Reset semplificato dell'ambiente"""
        # Reset dei flag del robot (se il metodo esiste)
        try:
            self.robot.reset_flags()
        except AttributeError:
            pass  # Il metodo potrebbe non esistere
        
        self.steps_count = 0
        self.consecutive_success_moves = 0
        self.collision_count = 0
        self.recent_positions.clear()
        
        # Reset a posizione origine - metodo semplificato
        self._reset_to_origin()
        
        # Aggiorna posizione corrente
        x, y, theta = self.robot.get_current_position()
        self.current_position = Position(x, y, theta)
        self.previous_position = self.current_position
        
        print(f"🔄 Reset: Robot a ({x:.2f}, {y:.2f})")
        return self.get_state()
    
    def _reset_to_origin(self):
        """Reset semplice alla posizione origine"""
        # Pubblica posizione origine
        self.robot.dds.publish('X', 0.0, self.robot.dds.DDS_TYPE_FLOAT)
        self.robot.dds.publish('Y', 0.0, self.robot.dds.DDS_TYPE_FLOAT)
        self.robot.dds.publish('Theta', 0.0, self.robot.dds.DDS_TYPE_FLOAT)
        
        # Aspetta che Godot processi il reset
        time.sleep(0.5)
        self.robot.dds.wait('tick')
    
    def get_state(self) -> Tuple[int, int]:
        """Stato semplificato: solo posizione X,Y discretizzata"""
        x, y, _ = self.robot.get_current_position()
        
        # Discretizzazione con griglia di 1 unità
        discrete_x = int(round(x))
        discrete_y = int(round(y))
        
        # Limita ai bounds del labirinto
        discrete_x = max(-5, min(5, discrete_x))
        discrete_y = max(-4, min(4, discrete_y))
        
        return (discrete_x, discrete_y)
    
    def _is_in_loop(self) -> bool:
        """Rilevamento loop semplificato"""
        if len(self.recent_positions) < 4:
            return False
            
        # Controlla se le ultime 4 posizioni si ripetono
        pos_counts = {}
        for pos in self.recent_positions:
            key = (round(pos.x, 1), round(pos.y, 1))
            pos_counts[key] = pos_counts.get(key, 0) + 1
        
        return max(pos_counts.values()) >= 3
    
    def step(self, action: int) -> Tuple[Tuple, float, bool, Dict]:
        """Esegui azione e calcola ricompensa progressiva"""
        self.steps_count += 1
        self.previous_position = self.current_position
        
        # Converti action in direction
        action_names = ["UP", "DOWN", "LEFT", "RIGHT"]
        direction = action_names[action]
        
        # Esegui movimento
        result = self.robot.move(direction)
        
        # Aggiorna posizione
        x, y, theta = self.robot.get_current_position()
        self.current_position = Position(x, y, theta)
        self.recent_positions.append(self.current_position)
        
        # Calcola ricompensa progressiva
        reward = self._calculate_progressive_reward(result)
        
        # Aggiorna contatori
        if result == MoveResult.SUCCESS:
            self.consecutive_success_moves += 1
        else:
            self.consecutive_success_moves = 0
            if result == MoveResult.COLLISION:
                self.collision_count += 1
        
        # Determina fine episodio
        done = self._check_done(result)
        
        # Info aggiuntive
        info = {
            'result': result,
            'steps': self.steps_count,
            'success_streak': self.consecutive_success_moves,
            'total_collisions': self.collision_count,
            'position': (x, y, theta)
        }
        
        return self.get_state(), reward, done, info
    
    def _calculate_progressive_reward(self, result: MoveResult) -> float:
        """Sistema di ricompense progressive basato su movimenti consecutivi"""
        # Ricompensa base
        base_reward = self.base_rewards[result]
        
        # Se è un successo, aggiungi bonus progressivo
        if result == MoveResult.SUCCESS:
            # Bonus crescente per movimenti consecutivi senza collisioni
            streak_bonus = min(
                self.consecutive_success_moves * self.success_streak_bonus,
                self.max_streak_bonus
            )
            total_reward = base_reward + streak_bonus
            
            # Bonus extra per lunghe sequenze
            if self.consecutive_success_moves >= 5:
                total_reward += 3.0  # Bonus per esplorazione prolungata
            if self.consecutive_success_moves >= 10:
                total_reward += 5.0  # Bonus ancora maggiore
            if self.consecutive_success_moves >= 15:
                total_reward += 8.0  # Bonus eccezionale
                
            if self.consecutive_success_moves % 5 == 0 and self.consecutive_success_moves > 0:
                print(f"🔥 Streak di {self.consecutive_success_moves} successi! "
                      f"Reward: {total_reward:.2f} (base: {base_reward:.1f} + bonus: {streak_bonus:.2f})")
                  
        else:
            total_reward = base_reward
            if result == MoveResult.COLLISION:
                print(f"💥 Collisione! Streak di {self.consecutive_success_moves} interrotta. "
                      f"Reward: {total_reward:.2f}")
            elif result == MoveResult.GOAL_REACHED:
                # Bonus extra se raggiungiamo il goal con una lunga streak
                streak_bonus = min(self.consecutive_success_moves * 2.0, 50.0)
                total_reward += streak_bonus
                print(f"🎯 GOAL RAGGIUNTO! Streak finale: {self.consecutive_success_moves}. "
                      f"Reward totale: {total_reward:.2f}")
        
        # Penalità per loop
        if self._is_in_loop():
            total_reward -= 5.0
            print(f"🔄 Loop rilevato! Penalità applicata.")
        
        # Piccola penalità per step per incoraggiare efficienza
        total_reward -= 0.1
        
        return total_reward
    
    def _check_done(self, result: MoveResult) -> bool:
        """Verifica fine episodio"""
        if result == MoveResult.GOAL_REACHED:
            return True
        if self.steps_count >= self.max_steps:
            print(f"⏱️ Timeout: {self.max_steps} steps raggiunti")
            return True
        if self.collision_count >= 8:  # Più tollerante
            print(f"🚫 Troppe collisioni: {self.collision_count}")
            return True
        if self._is_in_loop() and self.steps_count > 20:
            print(f"🔄 Episodio terminato per loop")
            return True
        return False


class SimpleQLearningAgent:
    """Agente Q-Learning semplificato"""
    
    def __init__(self, learning_rate: float = 0.15, discount_factor: float = 0.95,
                 epsilon: float = 0.9, epsilon_decay: float = 0.995, epsilon_min: float = 0.05):
        
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        
        # Q-table semplificata: stato -> [q_values per 4 azioni]
        self.q_table = {}
        self.n_actions = 4
        
        # Statistiche
        self.episode_rewards = []
        self.episode_steps = []
        self.success_episodes = []
    
    def get_q_values(self, state: Tuple) -> np.ndarray:
        """Ottieni Q-values per uno stato"""
        if state not in self.q_table:
            # Inizializza con valori piccoli positivi per incoraggiare esplorazione
            self.q_table[state] = np.random.uniform(0.0, 0.5, self.n_actions)
        return self.q_table[state]
    
    def choose_action(self, state: Tuple, training: bool = True) -> int:
        """Scelta azione epsilon-greedy semplificata"""
        if training and random.random() < self.epsilon:
            return random.randint(0, self.n_actions - 1)
        else:
            q_values = self.get_q_values(state)
            # In caso di parità, scegli casualmente tra le azioni migliori
            max_q = np.max(q_values)
            best_actions = np.where(q_values == max_q)[0]
            return int(np.random.choice(best_actions))
    
    def update_q_value(self, state: Tuple, action: int, reward: float, 
                      next_state: Tuple, done: bool = False):
        """Update Q-value con regola Q-learning standard"""
        current_q = self.get_q_values(state)[action]
        
        if done:
            target = reward
        else:
            next_q_values = self.get_q_values(next_state)
            target = reward + self.discount_factor * np.max(next_q_values)
        
        # Update con learning rate
        self.q_table[state][action] += self.learning_rate * (target - current_q)
    
    def decay_epsilon(self):
        """Riduci epsilon"""
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
    
    def save_model(self, filepath: str):
        """Salva modello"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        model_data = {
            'q_table': self.q_table,
            'epsilon': self.epsilon,
            'episode_rewards': self.episode_rewards,
            'episode_steps': self.episode_steps,
            'success_episodes': self.success_episodes,
            'hyperparameters': {
                'learning_rate': self.learning_rate,
                'discount_factor': self.discount_factor,
                'epsilon_decay': self.epsilon_decay,
                'epsilon_min': self.epsilon_min
            }
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        print(f"💾 Modello salvato: {len(self.q_table)} stati")
    
    def load_model(self, filepath: str) -> bool:
        """Carica modello"""
        if not os.path.exists(filepath):
            print(f"❌ File {filepath} non trovato")
            return False
        
        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
            
            self.q_table = model_data['q_table']
            self.epsilon = model_data.get('epsilon', self.epsilon)
            self.episode_rewards = model_data.get('episode_rewards', [])
            self.episode_steps = model_data.get('episode_steps', [])
            self.success_episodes = model_data.get('success_episodes', [])
            
            print(f"📁 Modello caricato: {len(self.q_table)} stati, epsilon: {self.epsilon:.3f}")
            return True
        except Exception as e:
            print(f"❌ Errore caricamento: {e}")
            return False


class SimpleRLTrainer:
    """Trainer semplificato con focus sulle ricompense progressive"""
    
    def __init__(self, dds, time_obj):
        self.dds = dds
        self.time = time_obj
        
        # Usa il DiffDriveRoboticAgent originale, ma NON avviare DDS nel robot
        # Modifica temporaneamente la classe per evitare il doppio start
        self.robot = self._create_robot(dds, time_obj)
        self.env = SimpleMazeEnvironment(self.robot)
        self.agent = SimpleQLearningAgent()
        self.model_filepath = "../models/maze_robot.pkl"
    
    def _create_robot(self, dds, time_obj):
        """Crea robot senza avviare DDS (già avviato nel main)"""
        robot = DiffDriveRoboticAgent(dds, time_obj)
        return robot
    
    def train(self, n_episodes: int = 300, save_every: int = 50):
        """Training semplificato con focus su ricompense progressive"""
        print(f"🚀 Training per {n_episodes} episodi con ricompense progressive")
        print(f"📈 Sistema: Bonus crescente per movimenti consecutivi senza collisioni")
        
        # Carica modello esistente se disponibile
        self.agent.load_model(self.model_filepath)
        
        # Sincronizza con Godot
        self.dds.wait('tick')
        print("✅ Connesso a Godot!")
        
        try:
            for episode in range(n_episodes):
                print(f"\n{'='*50}")
                print(f"📍 EPISODIO {episode + 1}/{n_episodes}")
                print(f"{'='*50}")
                
                # Reset ambiente
                state = self.env.reset()
                total_reward = 0
                done = False
                max_streak_in_episode = 0
                
                while not done:
                    # Scegli e esegui azione
                    action = self.agent.choose_action(state, training=True)
                    next_state, reward, done, info = self.env.step(action)
                    
                    # Update Q-learning
                    self.agent.update_q_value(state, action, reward, next_state, done)
                    
                    total_reward += reward
                    state = next_state
                    
                    # Traccia la streak massima dell'episodio
                    max_streak_in_episode = max(max_streak_in_episode, info['success_streak'])
                    
                    # Log progresso ogni 30 step
                    if info['steps'] % 30 == 0:
                        action_names = ["↑UP", "↓DOWN", "←LEFT", "→RIGHT"]
                        print(f"  Step {info['steps']}: {action_names[action]} → "
                              f"Pos {info['position'][:2]}, Streak: {info['success_streak']}, "
                              f"Reward: {reward:.1f}")
                
                # Statistiche episodio
                self.agent.episode_rewards.append(total_reward)
                self.agent.episode_steps.append(info['steps'])
                success = (info['result'] == MoveResult.GOAL_REACHED)
                self.agent.success_episodes.append(success)
                
                # Decay epsilon
                self.agent.decay_epsilon()
                
                # Log risultati
                symbol = "🎯" if success else "💥" if info['total_collisions'] > 2 else "⏱️"
                print(f"\n{symbol} Episodio completato:")
                print(f"  🏆 Reward totale: {total_reward:.2f}")
                print(f"  📏 Steps: {info['steps']}")
                print(f"  🔥 Max streak: {max_streak_in_episode}")
                print(f"  💥 Collisioni: {info['total_collisions']}")
                print(f"  🎲 Epsilon: {self.agent.epsilon:.3f}")
                
                # Calcola success rate recente
                if len(self.agent.success_episodes) >= 20:
                    recent_success = sum(self.agent.success_episodes[-20:]) / 20
                    print(f"  📊 Success rate (ultimi 20): {recent_success:.1%}")
                
                # Salva periodicamente
                if (episode + 1) % save_every == 0:
                    self.agent.save_model(self.model_filepath)
                    self._print_stats()
                    
        except KeyboardInterrupt:
            print(f"\n⚠️ Training interrotto")
        finally:
            self.agent.save_model(self.model_filepath)
            print(f"\n✅ Training completato!")
            self._print_final_stats()
    
    def test(self, n_episodes: int = 5):
        """Test dell'agente addestrato"""
        print(f"\n🧪 TEST - {n_episodes} episodi")
        
        if not self.agent.load_model(self.model_filepath):
            print("❌ Nessun modello trovato!")
            return
        
        # Disabilita esplorazione per test
        original_epsilon = self.agent.epsilon
        self.agent.epsilon = 0.0
        
        self.dds.wait('tick')
        
        successes = 0
        total_steps = 0
        total_max_streaks = 0
        
        try:
            for episode in range(n_episodes):
                print(f"\n📍 Test {episode + 1}/{n_episodes}")
                
                state = self.env.reset()
                done = False
                max_streak = 0
                
                while not done:
                    action = self.agent.choose_action(state, training=False)
                    state, reward, done, info = self.env.step(action)
                    
                    max_streak = max(max_streak, info['success_streak'])
                    
                    if info['steps'] % 20 == 0:
                        print(f"  Step {info['steps']}: {info['position'][:2]}, "
                              f"Streak: {info['success_streak']}")
                
                total_steps += info['steps']
                total_max_streaks += max_streak
                
                if info['result'] == MoveResult.GOAL_REACHED:
                    successes += 1
                    print(f"✅ Goal raggiunto in {info['steps']} steps! "
                          f"Max streak: {max_streak}")
                else:
                    print(f"❌ Test fallito: {info['result'].value}")
        
        finally:
            self.agent.epsilon = original_epsilon
            
            print(f"\n📊 RISULTATI TEST:")
            print(f"  🎯 Success rate: {successes}/{n_episodes} ({successes/n_episodes:.1%})")
            print(f"  👣 Steps medi: {total_steps/n_episodes:.1f}")
            print(f"  🔥 Streak media massima: {total_max_streaks/n_episodes:.1f}")
    
    def _print_stats(self):
        """Stampa statistiche periodiche"""
        if not self.agent.episode_rewards:
            return
            
        recent_rewards = self.agent.episode_rewards[-50:]
        recent_steps = self.agent.episode_steps[-50:]
        recent_success = self.agent.success_episodes[-50:]
        
        print(f"\n📊 STATISTICHE (ultimi 50 episodi):")
        print(f"  💰 Reward medio: {np.mean(recent_rewards):.2f}")
        print(f"  👣 Steps medi: {np.mean(recent_steps):.1f}")
        print(f"  🎯 Success rate: {sum(recent_success)/len(recent_success):.1%}")
        print(f"  🗺️ Stati esplorati: {len(self.agent.q_table)}")
    
    def _print_final_stats(self):
        """Statistiche finali"""
        if not self.agent.episode_rewards:
            return
            
        print(f"\n{'='*50}")
        print(f"🏁 STATISTICHE FINALI")
        print(f"{'='*50}")
        print(f"📈 Episodi totali: {len(self.agent.episode_rewards)}")
        print(f"🗺️ Stati esplorati: {len(self.agent.q_table)}")
        print(f"💰 Reward medio: {np.mean(self.agent.episode_rewards):.2f}")
        print(f"🏆 Reward massimo: {np.max(self.agent.episode_rewards):.2f}")
        
        if self.agent.success_episodes:
            total_success = sum(self.agent.success_episodes) / len(self.agent.success_episodes)
            print(f"🎯 Success rate totale: {total_success:.1%}")
            
            # Trova primo successo
            first_success = next((i for i, s in enumerate(self.agent.success_episodes) if s), None)
            if first_success is not None:
                print(f"🥇 Primo successo: episodio {first_success + 1}")


def main():
    dds = DDS()

    time_obj = Time()
    
    try:
        # Crea il trainer DOPO aver avviato DDS
        trainer = SimpleRLTrainer(dds, time_obj)
        
        while True:
            print(f"\n{'='*60}")
            print("🤖 ROBOT RL - SISTEMA CON RICOMPENSE PROGRESSIVE")
            print("   🔥 Bonus crescente per movimenti consecutivi senza collisioni")
            print(f"{'='*60}")
            print("1. 🎓 Train - Addestra agente")
            print("2. 🧪 Test - Testa agente")
            print("3. 📚 Continue - Continua training")
            print("4. 📊 Stats - Mostra statistiche")
            print("5. 🚪 Exit")
            
            choice = input("\n👉 Scelta (1-5): ").strip()
            
            if choice == "1":
                episodes = int(input("Episodi (default 250): ") or "250")
                trainer.train(n_episodes=episodes)
            elif choice == "2":
                tests = int(input("Test episodes (default 3): ") or "3")
                trainer.test(n_episodes=tests)
            elif choice == "3":
                episodes = int(input("Episodi aggiuntivi (default 100): ") or "100")
                trainer.train(n_episodes=episodes)
            elif choice == "4":
                if trainer.agent.load_model(trainer.model_filepath):
                    trainer._print_final_stats()
                else:
                    print("❌ Nessun modello trovato!")
            elif choice == "5":
                break
            else:
                print("❌ Opzione non valida")
    
    except KeyboardInterrupt:
        print(f"\n👋 Chiusura...")
    except Exception as e:
        print(f"\n❌ Errore: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            dds.stop()
        except:
            pass


if __name__ == "__main__":
    main()