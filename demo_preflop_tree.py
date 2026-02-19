#!/usr/bin/env python3
"""
Demo: Pre-flop Betting Tree with A* Search

Shows how A* searches over a tree of betting sequences (open -> 3-bet -> 4-bet)
instead of a flat list of bet sizes.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "Module 2"))

from preflop_betting_tree import a_star_preflop_tree


def main():
    print("\n" + "=" * 70)
    print("  PRE-FLOP BETTING TREE - A* Search Demo")
    print("  Tree: Hero opens -> Villain (fold/call/3-bet) -> Hero (fold/call/4-bet)")
    print("=" * 70)
    
    scenarios = [
        ("AA", (50, 50), "Tight", "Premium hand vs Tight opponent"),
        ("KAs", (50, 50), "Aggressive", "Strong hand vs Aggressive opponent"),
        ("TJs", (50, 50), "Loose", "Playable hand vs Loose opponent"),
        ("72o", (50, 50), "Tight", "Weak hand (should fold)"),
        ("AA", (20, 20), "Tight", "Premium hand with short stack"),
    ]
    
    for hand, stacks, opponent, desc in scenarios:
        result = a_star_preflop_tree(hand, stacks, opponent)
        print(f"\n📋 {desc}")
        print(f"   Hand: {hand}, Stacks: {stacks} BB, Opponent: {opponent}")
        print(f"   ✅ Action: {result['action']} {result['bet_size']:.1f}x BB" if result['action'] != 'fold' else "   ✅ Action: fold")
        print(f"   📊 EV: {result['ev']:.2f} BB")
        print(f"   🔍 Nodes explored: {result['nodes_explored']}")
        print(f"   📝 Path: {' -> '.join(result['path'])}")
    
    print("\n" + "=" * 70)
    print("  Why A* is relevant here:")
    print("  - Tree has multiple levels (open -> 3-bet -> 4-bet)")
    print("  - Each 'open' branch leads to a subtree (villain response -> hero response)")
    print("  - Heuristic estimates EV at each node to guide exploration")
    print("  - Memoization avoids recomputing subtrees")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
