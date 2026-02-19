#!/usr/bin/env python3
"""
Demo script for Module 2: Optimal Bet Sizing Search

This script demonstrates how Module 2 finds optimal bet sizes using
informed search algorithms (A*, IDA*, Beam Search).
"""

import sys
from pathlib import Path

# Add Module 2 to path
sys.path.insert(0, str(Path(__file__).parent / "Module 2"))

from bet_sizing_search import optimal_bet_sizing_search


def print_result(result, scenario):
    """Print the result of a bet sizing search."""
    print(f"\n📋 Scenario: {scenario}")
    print(f"✅ Action: {result['action']}")
    print(f"💰 Bet Size: {result['bet_size']:.1f}x BB")
    print(f"📊 Expected Value: {result['expected_value']:.2f} BB")
    print(f"💭 Reason: {result['reason']}")
    print(f"🔍 Search Algorithm: {result['search_algorithm']}")
    print(f"🎯 Module 1 Playable: {result['module1_result'].get('playable', False)}")


def main():
    """Run demos of Module 2."""
    print("\n" + "🎰" * 40)
    print("  MODULE 2 DEMO: Optimal Bet Sizing Search")
    print("  Using Informed Search Algorithms (A*, IDA*, Beam Search)")
    print("🎰" * 40)
    
    print("\n" + "=" * 80)
    print("  DEMO 1: Premium Hand (AA) from Button vs Tight Opponent")
    print("=" * 80)
    result = optimal_bet_sizing_search(
        "AA", "Button", (50, 50), "Tight", search_algorithm="a_star"
    )
    print_result(result, "AA from Button, 50 BB stacks, vs Tight opponent")
    
    print("\n" + "=" * 80)
    print("  DEMO 2: Strong Hand (KAs) vs Different Opponent Types")
    print("=" * 80)
    for opponent in ["Tight", "Loose", "Aggressive", "Passive"]:
        result = optimal_bet_sizing_search(
            "KAs", "Button", (50, 50), opponent, search_algorithm="a_star"
        )
        print_result(result, f"KAs from Button vs {opponent} opponent")
    
    print("\n" + "=" * 80)
    print("  DEMO 3: Different Search Algorithms")
    print("=" * 80)
    hand = "AA"
    position = "Button"
    stacks = (50, 50)
    opponent = "Tight"
    
    for algo in ["a_star", "ida_star", "beam_search"]:
        result = optimal_bet_sizing_search(
            hand, position, stacks, opponent, search_algorithm=algo
        )
        print_result(result, f"AA from Button using {algo}")
    
    print("\n" + "=" * 80)
    print("  DEMO 4: Unplayable Hand (Filtered by Module 1)")
    print("=" * 80)
    result = optimal_bet_sizing_search(
        "72o", "Button", (50, 50), "Tight", search_algorithm="a_star"
    )
    print_result(result, "72o from Button (weakest hand)")
    
    print("\n" + "=" * 80)
    print("  DEMO 5: Different Stack Sizes")
    print("=" * 80)
    for stacks in [(10, 10), (50, 50), (200, 200)]:
        result = optimal_bet_sizing_search(
            "AA", "Button", stacks, "Tight", search_algorithm="a_star"
        )
        print_result(result, f"AA from Button, {stacks[0]} BB stacks")
    
    print("\n" + "=" * 80)
    print("  ✅ All demos completed!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
