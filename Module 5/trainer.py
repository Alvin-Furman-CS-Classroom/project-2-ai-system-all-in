"""
Training utilities for Module 5 RL agent.
"""

from __future__ import annotations

from typing import Iterable, Tuple

from rl_agent import RLPokerAgent, State, Action


Transition = Tuple[State, Action, float, State, bool]


def train_from_transitions(
    agent: RLPokerAgent,
    transitions: Iterable[Transition],
) -> None:
    """Train the agent from an iterable of transitions."""
    for s, a, r, s2, done in transitions:
        agent.update(s, a, r, s2, done)

