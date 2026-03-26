"""
Module 5 RL agent (tabular Q-learning scaffold).
"""

from __future__ import annotations

import random
from collections import defaultdict
from typing import Dict, Tuple, List


Action = str
State = Tuple


class RLPokerAgent:
    """Simple epsilon-greedy tabular Q-learning agent."""

    def __init__(
        self,
        actions: List[Action],
        alpha: float = 0.1,
        gamma: float = 0.95,
        epsilon: float = 0.1,
    ) -> None:
        self.actions = actions
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.q: Dict[State, Dict[Action, float]] = defaultdict(
            lambda: {a: 0.0 for a in self.actions}
        )

    def select_action(self, state: State) -> Action:
        """Epsilon-greedy action selection."""
        if random.random() < self.epsilon:
            return random.choice(self.actions)
        values = self.q[state]
        best = max(values.values())
        best_actions = [a for a, v in values.items() if v == best]
        return random.choice(best_actions)

    def update(
        self,
        state: State,
        action: Action,
        reward: float,
        next_state: State,
        done: bool,
    ) -> None:
        """One-step Q-learning update."""
        q_sa = self.q[state][action]
        next_max = 0.0 if done else max(self.q[next_state].values())
        target = reward + self.gamma * next_max
        self.q[state][action] = q_sa + self.alpha * (target - q_sa)

