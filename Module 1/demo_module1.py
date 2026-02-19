#!/usr/bin/env python3
"""
Demo script for Module 1: Propositional Logic Hand Decider

This script demonstrates various scenarios showing how Module 1 evaluates
hand playability based on position, stack size, and opponent tendencies.
"""

import sys
from pathlib import Path

# Add Module 1 to path
sys.path.insert(0, str(Path(__file__).parent / "Module 1"))

from propositional_logic import propositional_logic_hand_decider


def print_demo_header(title):
    """Print a formatted header for each demo."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_result(result, scenario_description):
    """Print the result of a hand evaluation."""
    print(f"\n📋 Scenario: {scenario_description}")
    print(f"✅ Playable: {result['playable']}")
    print(f"💭 Reason: {result['reason']}")
    print(f"\n📊 Knowledge Base Summary:")
    print(f"   - Rules: {len(result['knowledge_base']['rules'])} CNF rules")
    print(f"   - Facts: {len(result['knowledge_base']['facts'])} derived facts")
    print(f"   - Inference Steps: {len(result['inference_chain'])} steps")
    
    # Show some key facts
    facts = result['knowledge_base']['facts']
    key_facts = ['position_valid', 'hand_strength_premium', 'hand_strength_strong', 
                 'hand_strength_playable', 'stack_ok', 'playable', 'final_playable']
    print(f"\n🔍 Key Facts:")
    for fact in key_facts:
        if fact in facts:
            print(f"   - {fact}: {facts[fact]}")


def demo_1_premium_hands():
    """Demo 1: Premium hands from different positions."""
    print_demo_header("DEMO 1: Premium Hands (AA, KK, AKs)")
    
    scenarios = [
        ("AA", "Button", 50, "Tight", "Pocket Aces from Button vs Tight opponent"),
        ("KK", "Button", 30, "Aggressive", "Pocket Kings from Button vs Aggressive opponent"),
        ("KAs", "Big_Blind", 25, "Unknown", "Ace-King suited from Big Blind vs Unknown opponent"),
    ]
    
    for hand, position, stack, opponent, desc in scenarios:
        result = propositional_logic_hand_decider(hand, position, stack, opponent)
        print_result(result, desc)


def demo_2_stack_size_impact():
    """Demo 2: How stack size affects playability."""
    print_demo_header("DEMO 2: Stack Size Impact on Hand Selection")
    
    hand = "KAs"  # Strong hand
    position = "Button"
    opponent = "Tight"
    
    stack_scenarios = [
        (5, "Ultra-short stack (<10 BB)"),
        (15, "Short stack (10-20 BB)"),
        (50, "Adequate stack (≥20 BB)"),
    ]
    
    for stack, desc in stack_scenarios:
        result = propositional_logic_hand_decider(hand, position, stack, opponent)
        print_result(result, f"{desc} - {hand} from {position}")


def demo_3_opponent_types():
    """Demo 3: How different opponent types affect playability."""
    print_demo_header("DEMO 3: Opponent Type Impact")
    
    hand = "TJs"  # Playable hand (rank ~50)
    position = "Button"
    stack = 50
    
    opponent_types = [
        ("Tight", "Tight opponent (plays fewer hands)"),
        ("Loose", "Loose opponent (plays many hands)"),
        ("Aggressive", "Aggressive opponent (bets/raises frequently)"),
        ("Passive", "Passive opponent (calls more, bets less)"),
        ("Unknown", "Unknown opponent (no read)"),
    ]
    
    for opponent, desc in opponent_types:
        result = propositional_logic_hand_decider(hand, position, stack, opponent)
        print_result(result, f"{desc} - {hand} from {position}")


def demo_4_position_comparison():
    """Demo 4: Button vs Big Blind position."""
    print_demo_header("DEMO 4: Position Comparison (Button vs Big Blind)")
    
    hand = "QJs"  # Strong hand (rank ~30)
    stack = 50
    opponent = "Unknown"
    
    positions = [
        ("Button", "Button position (acts last, more flexible)"),
        ("Big_Blind", "Big Blind position (acts first, less flexible)"),
    ]
    
    for position, desc in positions:
        result = propositional_logic_hand_decider(hand, position, stack, opponent)
        print_result(result, f"{desc} - {hand}")


def demo_5_edge_cases():
    """Demo 5: Edge cases and boundary conditions."""
    print_demo_header("DEMO 5: Edge Cases and Boundary Conditions")
    
    scenarios = [
        ("72o", "Button", 50, "Tight", "Weakest hand (23o) - should not be playable"),
        ("AA", "Button", 9, "Tight", "Premium hand with ultra-short stack (9 BB)"),
        ("AA", "Button", 10, "Tight", "Premium hand at stack threshold (10 BB)"),
        ("KAs", "Button", 20, "Tight", "Strong hand at stack threshold (20 BB)"),
        ("InvalidHand", "Button", 50, "Tight", "Invalid hand format"),
        ("AA", "InvalidPosition", 50, "Tight", "Invalid position"),
    ]
    
    for hand, position, stack, opponent, desc in scenarios:
        result = propositional_logic_hand_decider(hand, position, stack, opponent)
        print_result(result, desc)


def demo_6_inference_chain():
    """Demo 6: Show detailed inference chain."""
    print_demo_header("DEMO 6: Detailed Inference Chain")
    
    hand = "AA"
    position = "Button"
    stack = 5  # Ultra-short stack
    opponent = "Tight"
    
    result = propositional_logic_hand_decider(hand, position, stack, opponent)
    
    print(f"\n📋 Scenario: {hand} from {position} with {stack} BB vs {opponent} opponent")
    print(f"✅ Playable: {result['playable']}")
    print(f"💭 Reason: {result['reason']}")
    
    print(f"\n🔗 Inference Chain ({len(result['inference_chain'])} steps):")
    for i, step in enumerate(result['inference_chain'], 1):
        print(f"   {i}. {step}")
    
    print(f"\n📊 Knowledge Base Facts:")
    facts = result['knowledge_base']['facts']
    for fact, value in sorted(facts.items()):
        print(f"   - {fact}: {value}")


def main():
    """Run all demos."""
    print("\n" + "🎰" * 40)
    print("  MODULE 1 DEMO: Propositional Logic Hand Decider")
    print("  Heads-Up Pre-Flop Poker Strategy Analyzer")
    print("🎰" * 40)
    
    demo_1_premium_hands()
    demo_2_stack_size_impact()
    demo_3_opponent_types()
    demo_4_position_comparison()
    demo_5_edge_cases()
    demo_6_inference_chain()
    
    print("\n" + "=" * 80)
    print("  ✅ All demos completed!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
