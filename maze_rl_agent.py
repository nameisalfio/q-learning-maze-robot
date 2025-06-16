"""
Simple Q-learning agent that learns to escape a 10×10 maze.

• The maze is hard-coded (see MAZE_LAYOUT).
• During TRAINING the agent explores the maze for N_EPISODES episodes.
• In the TEST phase (greedy policy) the learned path is displayed.

Requirements
------------
python -m pip install numpy matplotlib

Run
---
python maze_rl_agent.py     # trains and then tests, opening two windows

Press any key in the training window to skip the live animation.
"""

import random
import time
from dataclasses import dataclass
from typing import List, Tuple

import matplotlib.pyplot as plt
import numpy as np

# --------------------------  Environment  ------------------------------------

# 1 = wall, 0 = free cell
MAZE_LAYOUT = np.array(
    [
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        [1, 1, 1, 1, 1, 0, 1, 0, 1, 0],
        [1, 0, 0, 0, 1, 0, 1, 0, 1, 0],
        [1, 0, 1, 0, 1, 0, 0, 0, 1, 0],
        [1, 0, 1, 0, 1, 1, 1, 0, 1, 0],
        [1, 0, 1, 0, 0, 0, 0, 0, 1, 0],
        [1, 0, 1, 1, 1, 1, 1, 1, 1, 0],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
    ],
    dtype=int,
)

ACTIONS = {
    0: (-1, 0),  # up
    1: (0, 1),  # right
    2: (1, 0),  # down
    3: (0, -1),  # left
}
NUM_ACTIONS = len(ACTIONS)
START_POS = (0, 0)
GOAL_POS = (9, 9)
MAX_STEPS = 500


@dataclass
class StepResult:
    state: Tuple[int, int]
    reward: float
    done: bool


class MazeEnv:
    def __init__(self):
        self.maze = MAZE_LAYOUT
        self.reset()

    def reset(self) -> Tuple[int, int]:
        self.pos = START_POS
        self.steps = 0
        return self.pos

    def step(self, action: int) -> StepResult:
        dy, dx = ACTIONS[action]
        y, x = self.pos
        ny, nx = y + dy, x + dx

        # Check bounds and walls
        if 0 <= ny < 10 and 0 <= nx < 10 and self.maze[ny, nx] == 0:
            self.pos = (ny, nx)
        else:
            # hit wall => stay in place, small penalty
            return StepResult(self.pos, -2.0, False)

        self.steps += 1
        if self.pos == GOAL_POS:
            return StepResult(self.pos, 10.0, True)
        if self.steps >= MAX_STEPS:
            return StepResult(self.pos, -10.0, True)
        return StepResult(self.pos, -1.0, False)


# --------------------------  Q-Learning agent  -------------------------------

class QAgent:
    def __init__(self, alpha=0.1, gamma=0.9, epsilon=1.0):
        # Q-table: 10×10×4
        self.Q = np.zeros((10, 10, NUM_ACTIONS))
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon

    def select_action(self, state: Tuple[int, int]) -> int:
        if random.random() < self.epsilon:
            return random.randint(0, NUM_ACTIONS - 1)
        y, x = state
        return int(np.argmax(self.Q[y, x]))

    def update(self, state, action, reward, next_state):
        y, x = state
        ny, nx = next_state
        best_next = np.max(self.Q[ny, nx])
        td_target = reward + self.gamma * best_next
        td_error = td_target - self.Q[y, x, action]
        self.Q[y, x, action] += self.alpha * td_error


# --------------------------  Visualisation  ----------------------------------

class MazeViewer:
    """Simple Matplotlib viewer."""

    def __init__(self, maze):
        self.maze = maze
        self.fig, self.ax = plt.subplots()
        self.ax.set_title("Training (press any key to skip)")
        self.img = self.ax.imshow(self.maze, cmap="binary")
        self.agent_dot, = self.ax.plot([], [], "ro")
        self.goal_dot, = self.ax.plot(GOAL_POS[1], GOAL_POS[0], "go")
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.skip_animation = False
        self.fig.canvas.mpl_connect("key_press_event", self._skip)

    def _skip(self, event):
        self.skip_animation = True

    def update(self, pos):
        if self.skip_animation:
            return
        y, x = pos
        self.agent_dot.set_data(x, y)
        plt.pause(0.001)

    def show_final(self, path: List[Tuple[int, int]], title="Test path"):
        self.ax.clear()
        self.ax.set_title(title)
        self.ax.imshow(self.maze, cmap="binary")
        ys, xs = zip(*path)
        self.ax.plot(xs, ys, "r.-", linewidth=2, markersize=8)
        self.ax.plot(xs[0], ys[0], "bo", label="start")
        self.ax.plot(xs[-1], ys[-1], "go", label="goal")
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.ax.legend()
        plt.show()


# --------------------------  Main routine  -----------------------------------

N_EPISODES = 5000
EPSILON_DECAY = 0.9995  # per episode
MIN_EPSILON = 0.05
DISPLAY_EVERY = 1  # episodes (set >1 to speed up)


def train(agent: QAgent, env: MazeEnv):
    viewer = MazeViewer(env.maze)
    steps_per_episode = []
    for ep in range(1, N_EPISODES + 1):
        state = env.reset()
        done = False
        steps = 0
        while not done:
            action = agent.select_action(state)
            result = env.step(action)
            agent.update(state, action, result.reward, result.state)
            state = result.state
            done = result.done
            steps += 1
            if ep % DISPLAY_EVERY == 0:
                viewer.update(state)
        # Decay epsilon
        agent.epsilon = max(agent.epsilon * EPSILON_DECAY, MIN_EPSILON)
        steps_per_episode.append(steps)

        if ep % 500 == 0:
            print(f"Episode {ep}/{N_EPISODES} – ε={agent.epsilon:.3f} – steps {steps}")
    plt.close(viewer.fig)
    return steps_per_episode


def test(agent: QAgent, env: MazeEnv):
    agent.epsilon = 0.0  # greedy
    state = env.reset()
    path = [state]
    for _ in range(MAX_STEPS):
        action = agent.select_action(state)
        result = env.step(action)
        state = result.state
        path.append(state)
        if result.done:
            break
    return path


if __name__ == "__main__":
    env = MazeEnv()
    agent = QAgent()

    print("Training…")
    train(agent, env)

    print("Testing…")
    test_path = test(agent, env)

    viewer = MazeViewer(env.maze)
    viewer.show_final(test_path, title="Learned path (test phase)")