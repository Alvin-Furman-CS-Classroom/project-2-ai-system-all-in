"""
Module 5 RL agent (tabular Q-learning scaffold).
"""

from __future__ import annotations

import pickle
import random
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union


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
        self._training_extra: Dict[str, Any] = {}

    def select_action(self, state: State) -> Action:
        """Epsilon-greedy over the full discrete set (no legality mask)."""
        if random.random() < self.epsilon:
            return random.choice(self.actions)
        values = self.q[state]
        best = max(values.values())
        best_actions = [a for a, v in values.items() if v == best]
        return random.choice(best_actions)

    def select_action_masked(self, state: State, legal_buckets: Sequence[str]) -> Action:
        """
        Epsilon-greedy restricted to buckets that are legal / non-redundant for this spot.

        Exploration draws uniformly from ``legal_buckets``; exploitation picks the
        highest-Q bucket among those (ties broken uniformly).
        """
        if not legal_buckets:
            return self.select_action(state)
        lb = [b for b in legal_buckets if b in self.actions]
        if not lb:
            return self.select_action(state)
        if random.random() < self.epsilon:
            return random.choice(lb)
        values = self.q[state]
        best_val = max(values.get(b, 0.0) for b in lb)
        best = [b for b in lb if values.get(b, 0.0) == best_val]
        return random.choice(best)

    def select_action_masked_with_bonus(
        self,
        state: State,
        legal_buckets: Sequence[str],
        visit_counts: Dict[Tuple[State, Action], int],
        bonus_c: float,
    ) -> Action:
        """
        Epsilon-greedy on legal buckets with count-based exploration bonus.

        Score: Q(s,a) + bonus_c / sqrt(1 + N(s,a))
        """
        if bonus_c <= 0.0:
            return self.select_action_masked(state, legal_buckets)
        lb = [b for b in legal_buckets if b in self.actions]
        if not lb:
            return self.select_action(state)
        if random.random() < self.epsilon:
            return random.choice(lb)
        values = self.q[state]
        scored = []
        for b in lb:
            n = visit_counts.get((state, b), 0)
            score = values.get(b, 0.0) + (bonus_c / ((1 + n) ** 0.5))
            scored.append((b, score))
        best_val = max(sc for _, sc in scored)
        best = [b for b, sc in scored if sc == best_val]
        return random.choice(best)

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

    def update_monte_carlo(self, state: State, action: Action, g: float) -> None:
        """Every-visit Monte Carlo target ``g`` (e.g. hand net BB for the acting player)."""
        q_sa = self.q[state][action]
        self.q[state][action] = q_sa + self.alpha * (g - q_sa)

    def save(self, path: Union[str, Path], extra: Optional[Dict[str, Any]] = None) -> None:
        """
        Persist Q-table and hyperparameters for cheap reload at inference time.

        Optional ``extra`` (e.g. ``final_button``, ``episodes_completed``) is stored for
        long-run training scripts that resume with correct dealer alternation and epsilon index.

        Uses pickle (tuple state keys). Only load files you trust.
        """
        p = Path(path)
        q_plain: Dict[State, Dict[Action, float]] = {k: dict(v) for k, v in self.q.items()}
        payload = {
            "version": 1,
            "actions": list(self.actions),
            "alpha": self.alpha,
            "gamma": self.gamma,
            "epsilon": self.epsilon,
            "q": q_plain,
            "extra": dict(extra) if extra else {},
        }
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("wb") as f:
            pickle.dump(payload, f, protocol=pickle.HIGHEST_PROTOCOL)

    @classmethod
    def load(cls, path: Union[str, Path]) -> "RLPokerAgent":
        """Load a policy saved with :meth:`save`. Set ``epsilon`` on the result for eval vs explore."""
        with Path(path).open("rb") as f:
            payload = pickle.load(f)
        required = ("actions", "alpha", "gamma", "epsilon", "q")
        if not isinstance(payload, dict) or any(k not in payload for k in required):
            raise ValueError("Invalid policy file: missing keys or wrong format")
        if int(payload.get("version", 1)) != 1:
            raise ValueError(f"Unsupported policy version: {payload.get('version')!r}")
        agent = cls(
            actions=list(payload["actions"]),
            alpha=float(payload["alpha"]),
            gamma=float(payload["gamma"]),
            epsilon=float(payload["epsilon"]),
        )
        for k, row in payload["q"].items():
            merged = {a: float(row.get(a, 0.0)) for a in agent.actions}
            agent.q[k] = merged
        agent._training_extra = dict(payload.get("extra") or {})
        return agent

