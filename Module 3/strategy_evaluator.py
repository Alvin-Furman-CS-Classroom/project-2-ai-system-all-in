"""
Evaluate an opening-action strategy via Monte Carlo simulation.

A strategy is a mapping from hand (or hand strength/range) to recommended
opening action (fold or bet size). This module computes the value of the strategy
and confidence intervals using simulation only—no Module 2 or EV formulas.
"""

from __future__ import annotations

from typing import Dict, Tuple, Optional

from monte_carlo_simulator import run_simulation_for_strategy


def evaluate_strategy(
    strategy: Dict[str, float],
    position: str,
    stack_sizes: Tuple[int, int],
    opponent_tendency: str,
    num_trials: int = 1000,
    confidence_level: float = 0.95,
    seed: Optional[int] = None,
) -> Dict:
    """
    Evaluate a strategy (hand -> opening bet size; 0 or sentinel = fold) using
    Monte Carlo simulation.

    Args:
        strategy: Dict mapping hand notation to opening bet size in BB (0 = fold).
        position: "Button" or "Big Blind".
        stack_sizes: (your_stack, opponent_stack) in BB.
        opponent_tendency: Opponent tendency category.
        num_trials: Number of trials per hand.
        confidence_level: Currently unused (we always return a 95% CI).
        seed: Random seed.

    Returns:
        Dict with:
        - "expected_value": overall strategy value (from simulation).
        - "confidence_interval": (lower, upper) for strategy value.
        - "per_hand_ev": dict hand -> value estimate.
        - "per_hand_results": raw per-hand simulation results.
        - "strategy": the input strategy.
    """
    # We treat num_trials as the number of trials per hand.
    sim_result = run_simulation_for_strategy(
        strategy=strategy,
        position=position,
        stack_sizes=stack_sizes,
        opponent_tendency=opponent_tendency,
        num_trials_per_hand=num_trials,
        hands=None,
        seed=seed,
    )

    per_hand_ev = {
        hand: res["value_estimate"]
        for hand, res in sim_result["per_hand_results"].items()
    }

    return {
        "expected_value": sim_result["expected_value"],
        "confidence_interval": sim_result["confidence_interval"],
        "per_hand_ev": per_hand_ev,
        "per_hand_results": sim_result["per_hand_results"],
        "strategy": strategy,
    }


def strategy_value_summary(
    strategy: Dict[str, float],
    position: str,
    stack_sizes: Tuple[int, int],
    opponent_tendency: str,
    num_trials: int = 500,
    seed: Optional[int] = None,
) -> Dict:
    """
    Return a summary of strategy value and confidence intervals suitable
    for output to Module 4 or reporting. Value from Monte Carlo only.

    Returns:
        Dict with expected_value, confidence_interval, and optional
        list of (hand, action, value_estimate) for key hands.
    """
    result = evaluate_strategy(
        strategy=strategy,
        position=position,
        stack_sizes=stack_sizes,
        opponent_tendency=opponent_tendency,
        num_trials=num_trials,
        seed=seed,
    )

    summary_rows = [
        {
            "hand": hand,
            "bet_size": strategy.get(hand, 0.0),
            "value_estimate": ev,
        }
        for hand, ev in result["per_hand_ev"].items()
    ]

    return {
        "expected_value": result["expected_value"],
        "confidence_interval": result["confidence_interval"],
        "hands": summary_rows,
    }
