#!/usr/bin/env python3
"""
Demo: bot (seat 1) decision via local Ollama after human completes blind call.

Requires Ollama running locally (`ollama serve`) with model available (default: llama3.2).

Usage (from project root):
  ollama serve
  # optional: OLLAMA_MODEL=llama3.2 OLLAMA_URL=http://127.0.0.1:11434
  python3 "Module 4/demo_module4.py"
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_M4 = Path(__file__).resolve().parent
if str(_M4) not in sys.path:
    sys.path.insert(0, str(_M4))

from game_engine.hu_preflop import apply_action, legal_actions, new_hand
from game_engine.mc_bot import hole_cards_to_mc_hand


def main() -> None:
    rng = random.Random(42)
    state = new_hand([2000, 2000], rng=rng, button=0)
    # Seat 0 (button) completes to the big blind
    apply_action(state, {"kind": "call", "amount": state.to_call(0)})
    assert state.actor == 1

    legal = legal_actions(state)
    c0, c1 = state.hole_cards[1]
    hand = hole_cards_to_mc_hand(c0, c1)

    from llm_policy import choose_preflop_action

    action = choose_preflop_action(state, hand, legal, rng)
    print("Bot hand:", hand)
    print("Legal count:", len(legal))
    print("Chosen action:", action)


if __name__ == "__main__":
    main()
