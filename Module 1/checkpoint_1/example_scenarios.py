#!/usr/bin/env python3
"""
Run example scenarios through Module 1's propositional_logic_hand_decider.
"""

import os
import importlib.util
from pprint import pprint

# Load Module 1/propositional_logic.py via its file path
ROOT = os.path.dirname(__file__)
MODULE_PATH = os.path.join(ROOT, "Module 1", "propositional_logic.py")

spec = importlib.util.spec_from_file_location("module1_logic", MODULE_PATH)
module1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module1)

# Convenience alias
decide = module1.propositional_logic_hand_decider

scenarios = [
    # (hand, position, stack_size, opponent_tendency, label)
    ("AKs",    "Button",    50, "Unknown",   "Premium BTN vs Unknown, deep stack"),
    ("TT",     "Big Blind", 25, "Tight",     "Medium pair BB vs Tight, mid stack"),
    ("45s",    "Big Blind", 15, "Tight",     "Low suited connector BB vs Tight, 15 BB"),
    ("AQo",    "Button",    8,  "Aggressive","AQo BTN vs Aggressive, 8 BB"),
    ("JTo",    "Button",    30, "Passive",   "JTo BTN vs Passive, 30 BB"),
]

for hand, pos, stack, opp, label in scenarios:
    print("\n" + "=" * 80)
    print(f"Scenario: {label}")
    print(f"Input: hand={hand}, position={pos}, stack_size={stack}, opponent={opp}")
    result = decide(hand=hand, position=pos, stack_size=stack, opponent_tendency=opp)

    print(f"\nPlayable? {result['playable']}")
    print(f"Reason:   {result['reason']}\n")

    print("Inference chain (first 10 steps):")
    for step in result["inference_chain"][:10]:
        print("  -", step)

    # If you want to see the full KB structure, uncomment:
    # print("\nKnowledge base snapshot:")
    # pprint(result["knowledge_base"])

print("\nDone.")