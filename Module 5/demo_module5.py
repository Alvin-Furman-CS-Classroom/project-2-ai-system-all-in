#!/usr/bin/env python3
"""
Demo script for Module 5: RL adaptive poker agent.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add Module 5 directory to path so imports work
_module5_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(_module5_dir))

from rl_agent import RLPokerAgent
from state_encoder import encode_state
from trainer import train_from_transitions


def main() -> None:
    print("\n" + "🤖" * 40)
    print("  MODULE 5 DEMO: Reinforcement Learning Agent")
    print("🤖" * 40)

    actions = ["fold", "call", "raise_small", "raise_large"]
    agent = RLPokerAgent(actions=actions, alpha=0.1, gamma=0.95, epsilon=0.1)

    # Tiny toy transition set (placeholder). Replace with real game logs.
    s1 = encode_state(
        {
            "hand": "AA",
            "position": "Button",
            "stack_bb": 50,
            "opponent_tendency": "Tight",
            "to_call_bb": 0.0,
            "pot_bb": 1.5,
        }
    )
    s2 = encode_state(
        {
            "hand": "72o",
            "position": "Button",
            "stack_bb": 50,
            "opponent_tendency": "Aggressive",
            "to_call_bb": 2.0,
            "pot_bb": 3.5,
        }
    )
    transitions = [
        (s1, "raise_large", 1.5, s1, True),
        (s1, "call", 0.8, s2, False),
        (s2, "fold", -0.2, s2, True),
    ]
    train_from_transitions(agent, transitions)

    print("\nSample policy decisions:")
    print(f"  - State AA/Button/Tight: {agent.select_action(s1)}")
    print(f"  - State 72o/Button/Aggressive: {agent.select_action(s2)}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()

