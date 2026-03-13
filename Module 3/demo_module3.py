#!/usr/bin/env python3
"""
Demo script for Module 3: Monte Carlo Optimal Opening Actions

Shows how Module 3 uses Monte Carlo simulation only to compute optimal opening
actions. Outputs strategy valueand confidence intervals.
"""

import sys
from pathlib import Path

# Add Module 3 directory to path so imports work
_module3_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(_module3_dir))

from bet_sizing_optimizer import optimize_opening_actions


def main():
    print("\n" + "🎲" * 40)
    print("  MODULE 3 DEMO: Monte Carlo Optimal Opening Actions")
    print("🎲" * 40)

    scenarios = [
        ("Button", (50, 50), "Tight", ["AA", "KK", "44", "AKs", "72o"]),
        ("Button", (50, 50), "Loose", ["AA", "44", "AKs", "AJo", "72o"]),
        ("Button", (50, 50), "Aggressive", ["AA", "44", "KQs", "T9s", "72o"]),
    ]

    for position, stacks, opponent, hands in scenarios:
        print("\n" + "=" * 80)
        print(f"Scenario: {position}, stacks={stacks} BB, opponent={opponent}")
        print("=" * 80)

        result = optimize_opening_actions(
            position=position,
            stack_sizes=stacks,
            opponent_tendency=opponent,
            hands=hands,
            candidate_bet_sizes=[2.0, 2.5, 3.0, 4.0, 5.0],
            num_simulations=500,
            seed=42,
        )

        strategy = result["optimized_strategy"]
        ev = result["expected_value"]
        ci_low, ci_high = result["confidence_interval"]

        print("\nRecommended opening actions (0.0 = fold):")
        for hand in hands:
            bet = strategy.get(hand, 0.0)
            if bet <= 0.0:
                print(f"  - {hand}: fold")
            else:
                print(f"  - {hand}: open {bet:.1f}x BB")

        print(f"\nEstimated strategy value: {ev:.3f} BB/hand")
        print(f"95% CI: [{ci_low:.3f}, {ci_high:.3f}]")

    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
