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
from RoboticAgent import DiffDriveRoboticAgent, MoveResult
from lib.dds.dds import DDS
from lib.utils.time import Time


@dataclass
class Position:
    x: float
    y: float
    theta: float
    
    def distance_to(self, other: 'Position') -> float:
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)


class MazeEnvironment:
    def __init__(self, robot_agent):
        self.robot = robot_agent
        self.current_position = None
        self.previous_position = None
        self.steps_count = 0
        self.max_steps = 100
        self.consecutive_success_moves = 0
        self.collision_count = 0
        self.recent_positions = deque(maxlen=6)
        self.visited_states = {}
        
        self.base_rewards = {
            MoveResult.SUCCESS: 5.0,
            MoveResult.COLLISION: -10.0,
            MoveResult.GOAL_REACHED: 100.0,
            MoveResult.TIMEOUT: -5.0,
        }
        
    def reset(self) -> Tuple:
        self.steps_count = 0
        self.consecutive_success_moves = 0
        self.collision_count = 0
        self.recent_positions.clear()
        
        self.robot.dds.publish('X', 0.0, self.robot.dds.DDS_TYPE_FLOAT)
        self.robot.dds.publish('Y', 0.0, self.robot.dds.DDS_TYPE_FLOAT)
        self.robot.dds.publish('Theta', 0.0, self.robot.dds.DDS_TYPE_FLOAT)
        
        time.sleep(0.5)
        self.robot.dds.wait('tick')
        
        x, y, theta = self.robot.get_current_position()
        self.current_position = Position(x, y, theta)
        self.previous_position = self.current_position
        
        print(f"Reset: Robot a ({x:.2f}, {y:.2f})")
        return self.get_state()
    
    def get_state(self) -> Tuple[int, int]:
        x, y, _ = self.robot.get_current_position()
        discrete_x = int(round(x / 10))
        discrete_y = int(round(y / 10))
        discrete_x = max(-5, min(5, discrete_x))
        discrete_y = max(-5, min(5, discrete_y))
        return (discrete_x, discrete_y)
    
    def step(self, action: int) -> Tuple[Tuple, float, bool, Dict]:
        self.steps_count += 1
        self.previous_position = self.current_position
        
        action_names = ["UP", "DOWN", "LEFT", "RIGHT"]
        direction = action_names[action]
        
        result = self.robot.move(direction)
        
        x, y, theta = self.robot.get_current_position()
        self.current_position = Position(x, y, theta)
        self.recent_positions.append(self.current_position)
        
        reward = self._calculate_reward(result)
        
        if result == MoveResult.SUCCESS:
            self.consecutive_success_moves += 1
        else:
            self.consecutive_success_moves = 0
            if result == MoveResult.COLLISION:
                self.collision_count += 1
        
        done = self._check_done(result)
        
        info = {
            'result': result,
            'steps': self.steps_count,
            'success_streak': self.consecutive_success_moves,
            'total_collisions': self.collision_count,
            'position': (x, y, theta)
        }
        
        return self.get_state(), reward, done, info
    
    def _calculate_reward(self, result: MoveResult) -> float:
        base_reward = self.base_rewards[result]
        
        if result == MoveResult.SUCCESS:
            streak_bonus = min(self.consecutive_success_moves * 2.0, 20.0)
            total_reward = base_reward + streak_bonus
        else:
            total_reward = base_reward
            if result == MoveResult.GOAL_REACHED:
                streak_bonus = min(self.consecutive_success_moves * 3.0, 50.0)
                total_reward += streak_bonus
        
        if self._is_in_loop():
            total_reward -= 8.0
        
        current_state = self.get_state()
        visits = self.visited_states.get(current_state, 0)
        self.visited_states[current_state] = visits + 1
        
        if visits == 0:
            total_reward += 3.0
        elif visits > 5:
            total_reward -= 2.0
        
        return total_reward
    
    def _is_in_loop(self) -> bool:
        if len(self.recent_positions) < 4:
            return False
        pos_counts = {}
        for pos in self.recent_positions:
            key = (round(pos.x / 10), round(pos.y / 10))
            pos_counts[key] = pos_counts.get(key, 0) + 1
        return max(pos_counts.values()) >= 3
    
    def _check_done(self, result: MoveResult) -> bool:
        if result == MoveResult.GOAL_REACHED:
            return True
        if self.steps_count >= self.max_steps:
            return True
        if self.collision_count >= 10:
            return True
        if self._is_in_loop() and self.steps_count > 15:
            return True
        return False


class QLearningAgent:
    def __init__(self, learning_rate: float = 0.1, discount_factor: float = 0.95,
                 epsilon: float = 0.8, epsilon_decay: float = 0.995, epsilon_min: float = 0.1):
        
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        
        self.q_table = {}
        self.n_actions = 4
        self.action_counts = {}
        
        self.episode_rewards = []
        self.episode_steps = []
        self.success_episodes = []
    
    def get_q_values(self, state: Tuple) -> np.ndarray:
        if state not in self.q_table:
            self.q_table[state] = np.random.uniform(0.1, 1.0, self.n_actions)
            self.action_counts[state] = np.zeros(self.n_actions)
        return self.q_table[state]
    
    def choose_action(self, state: Tuple, training: bool = True) -> int:
        if not training:
            q_values = self.get_q_values(state)
            return int(np.argmax(q_values))
        
        if random.random() < self.epsilon:
            q_values = self.get_q_values(state)
            action_counts = self.action_counts[state]
            
            untried_actions = np.where(action_counts == 0)[0]
            if len(untried_actions) > 0:
                action = int(np.random.choice(untried_actions))
            else:
                total_visits = np.sum(action_counts)
                ucb_values = q_values + 2.0 * np.sqrt(np.log(total_visits + 1) / (action_counts + 1))
                action = int(np.argmax(ucb_values))
        else:
            q_values = self.get_q_values(state)
            action = int(np.argmax(q_values))
        
        self.action_counts[state][action] += 1
        return action
    
    def update_q_value(self, state: Tuple, action: int, reward: float, 
                      next_state: Tuple, done: bool = False):
        current_q = self.get_q_values(state)[action]
        
        if done:
            target = reward
        else:
            next_q_values = self.get_q_values(next_state)
            target = reward + self.discount_factor * np.max(next_q_values)
        
        self.q_table[state][action] += self.learning_rate * (target - current_q)
    
    def decay_epsilon(self):
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
    
    def save_model(self, filepath: str):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        model_data = {
            'q_table': self.q_table,
            'action_counts': self.action_counts,
            'epsilon': self.epsilon,
            'episode_rewards': self.episode_rewards,
            'episode_steps': self.episode_steps,
            'success_episodes': self.success_episodes,
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        print(f"Modello salvato: {len(self.q_table)} stati")
    
    def load_model(self, filepath: str) -> bool:
        if not os.path.exists(filepath):
            print(f"File {filepath} non trovato")
            return False
        
        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
            
            self.q_table = model_data['q_table']
            self.action_counts = model_data.get('action_counts', {})
            self.epsilon = model_data.get('epsilon', self.epsilon)
            self.episode_rewards = model_data.get('episode_rewards', [])
            self.episode_steps = model_data.get('episode_steps', [])
            self.success_episodes = model_data.get('success_episodes', [])
            
            for state in self.q_table:
                if state not in self.action_counts:
                    self.action_counts[state] = np.zeros(self.n_actions)
            
            print(f"Modello caricato: {len(self.q_table)} stati, epsilon: {self.epsilon:.3f}")
            return True
        except Exception as e:
            print(f"Errore caricamento: {e}")
            return False


class RLTrainer:
    def __init__(self, dds, time_obj):
        self.dds = dds
        self.time = time_obj
        self.robot = DiffDriveRoboticAgent(dds, time_obj)
        self.env = MazeEnvironment(self.robot)
        self.agent = QLearningAgent()
        self.model_filepath = "../models/maze_robot.pkl"
    
    def train(self, n_episodes: int = 200, save_every: int = 50):
        print(f"Training per {n_episodes} episodi")
        
        self.agent.load_model(self.model_filepath)
        self.dds.wait('tick')
        print("Connesso a Godot!")
        
        try:
            for episode in range(n_episodes):
                print(f"\nEpisodio {episode + 1}/{n_episodes}")
                
                state = self.env.reset()
                total_reward = 0
                done = False
                max_streak = 0
                
                while not done:
                    action = self.agent.choose_action(state, training=True)
                    next_state, reward, done, info = self.env.step(action)
                    
                    self.agent.update_q_value(state, action, reward, next_state, done)
                    
                    total_reward += reward
                    state = next_state
                    max_streak = max(max_streak, info['success_streak'])
                
                self.agent.episode_rewards.append(total_reward)
                self.agent.episode_steps.append(info['steps'])
                success = (info['result'] == MoveResult.GOAL_REACHED)
                self.agent.success_episodes.append(success)
                
                self.agent.decay_epsilon()
                
                symbol = "GOAL" if success else "FAIL"
                print(f"{symbol}: Reward: {total_reward:.1f}, Steps: {info['steps']}, "
                      f"Max streak: {max_streak}, Epsilon: {self.agent.epsilon:.3f}")
                
                if len(self.agent.success_episodes) >= 20:
                    recent_success = sum(self.agent.success_episodes[-20:]) / 20
                    print(f"Success rate (ultimi 20): {recent_success:.1%}")
                
                if (episode + 1) % save_every == 0:
                    self.agent.save_model(self.model_filepath)
                    self._print_stats()
                    
        except KeyboardInterrupt:
            print("Training interrotto")
        finally:
            self.agent.save_model(self.model_filepath)
            print("Training completato!")
            self._print_final_stats()
    
    def test(self, n_episodes: int = 5):
        print(f"Test - {n_episodes} episodi")
        
        if not self.agent.load_model(self.model_filepath):
            print("Nessun modello trovato!")
            return
        
        original_epsilon = self.agent.epsilon
        self.agent.epsilon = 0.0
        
        self.dds.wait('tick')
        
        successes = 0
        total_steps = 0
        
        try:
            for episode in range(n_episodes):
                print(f"\nTest {episode + 1}/{n_episodes}")
                
                state = self.env.reset()
                done = False
                
                while not done:
                    action = self.agent.choose_action(state, training=False)
                    state, reward, done, info = self.env.step(action)
                
                total_steps += info['steps']
                
                if info['result'] == MoveResult.GOAL_REACHED:
                    successes += 1
                    print(f"Goal raggiunto in {info['steps']} steps!")
                else:
                    print(f"Test fallito: {info['result'].value}")
        
        finally:
            self.agent.epsilon = original_epsilon
            
            print(f"\nRisultati test:")
            print(f"Success rate: {successes}/{n_episodes} ({successes/n_episodes:.1%})")
            print(f"Steps medi: {total_steps/n_episodes:.1f}")
    
    def _print_stats(self):
        if not self.agent.episode_rewards:
            return
            
        recent_rewards = self.agent.episode_rewards[-50:]
        recent_steps = self.agent.episode_steps[-50:]
        recent_success = self.agent.success_episodes[-50:]
        
        print(f"\nStatistiche (ultimi 50 episodi):")
        print(f"Reward medio: {np.mean(recent_rewards):.2f}")
        print(f"Steps medi: {np.mean(recent_steps):.1f}")
        print(f"Success rate: {sum(recent_success)/len(recent_success):.1%}")
        print(f"Stati esplorati: {len(self.agent.q_table)}")
    
    def _print_final_stats(self):
        if not self.agent.episode_rewards:
            return
            
        print(f"\nStatistiche finali:")
        print(f"Episodi totali: {len(self.agent.episode_rewards)}")
        print(f"Stati esplorati: {len(self.agent.q_table)}")
        print(f"Reward medio: {np.mean(self.agent.episode_rewards):.2f}")
        print(f"Reward massimo: {np.max(self.agent.episode_rewards):.2f}")
        
        if self.agent.success_episodes:
            total_success = sum(self.agent.success_episodes) / len(self.agent.success_episodes)
            print(f"Success rate totale: {total_success:.1%}")


def main():
    dds = DDS()
    time_obj = Time()
    
    try:
        trainer = RLTrainer(dds, time_obj)
        
        while True:
            print(f"\n{'='*50}")
            print("ROBOT RL MAZE SOLVER")
            print(f"{'='*50}")
            print("1. 🎓 Train - Addestra nuovo agente")
            print("2. 🧪 Test - Testa agente addestrato")
            print("3. 📚 Continue - Continua addestramento")
            print("4. 📊 Stats - Mostra statistiche modello")
            print("5. 🚪 Exit - Esci dal programma")
            
            choice = input("\nScelta (1-5): ").strip()
            
            if choice == "1":
                episodes = int(input("Episodi (default 200): ") or "200")
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
                    print("Nessun modello trovato!")
            elif choice == "5":
                break
            else:
                print("Opzione non valida")
    
    except KeyboardInterrupt:
        print("Chiusura...")
    except Exception as e:
        print(f"Errore: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            dds.stop()
        except:
            pass


if __name__ == "__main__":
    main()