"""
Prompt templates for Module 4 LLM policy: index pick into legal actions.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List


SYSTEM_INSTRUCTION = """You are a heads-up No-Limit Texas Hold'em advisor.
You may be asked on pre-flop only or on any street (preflop through river) with board cards shown.
You must choose exactly one legal action by its index from the list provided.
Do not invent actions not in the list. Use solid poker reasoning for stacks, pot, board, and street.
Return only structured JSON matching the schema (option_index, optional reason)."""


def build_user_prompt(snapshot: Dict[str, Any], legal_actions: List[Dict[str, Any]]) -> str:
    """Human-readable game snapshot plus enumerated legal actions."""
    lines = [
        "Game state (JSON):",
        json.dumps(snapshot, indent=2),
        "",
        "Legal actions (choose exactly one by index):",
    ]
    for i, a in enumerate(legal_actions):
        lines.append(f"  [{i}] {json.dumps(a)}")
    lines.append(
        "Use option_index exactly as the [i] labels (0 = first action, 1 = second, etc.)."
    )
    lines.append('Respond with JSON: {"option_index": <int>, "reason": "..."}')
    return "\n".join(lines)
