"""
State encoder for Module 5 RL agent.

Converts poker context into a compact, hashable state representation suitable
for tabular RL.
"""

from __future__ import annotations

from typing import Dict, Any, Tuple


def encode_state(context: Dict[str, Any]) -> Tuple:
    """
    Encode a game context dictionary into a tuple state.

    Expected keys (example):
      hand, position, stack_bb, opponent_tendency, to_call_bb, pot_bb
    """
    return (
        context.get("hand", "UNKNOWN"),
        context.get("position", "UNKNOWN"),
        int(context.get("stack_bb", 0)),
        context.get("opponent_tendency", "Unknown"),
        float(context.get("to_call_bb", 0.0)),
        float(context.get("pot_bb", 0.0)),
    )

