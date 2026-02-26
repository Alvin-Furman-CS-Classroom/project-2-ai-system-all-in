"""
Evaluate an opening-action strategy via Monte Carlo simulation.

A strategy is a mapping from hand (or hand strength/range) to recommended
opening action (fold or bet size). This module computes the value of the strategy
and confidence intervals using simulation only—no Module 2 or EV formulas.
"""

from typing import Dict, Tuple, Optional, List


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
    Monte Carlo simulation only. No Module 2 or heuristics.

    Args:
        strategy: Dict mapping hand notation to opening bet size in BB (0 = fold).
        position: "Button" or "Big Blind".
        stack_sizes: (your_stack, opponent_stack) in BB.
        opponent_tendency: Opponent tendency category.
        num_trials: Number of trials per hand (or total, depending on design).
        confidence_level: e.g. 0.95 for 95% CI.
        seed: Random seed.

    Returns:
        Dict with:
        - "expected_value": overall strategy value (from simulation).
        - "confidence_interval": (lower, upper) for strategy value.
        - "per_hand_ev": optional dict hand -> value estimate.
        - "strategy": the input strategy (or refined version).
    """
    # TODO: Use monte_carlo_simulator to run simulations; aggregate value and CI.
    # No Module 2 or EV formulas.
    raise NotImplementedError("evaluate_strategy not yet implemented")


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
    # TODO: Call evaluate_strategy and format for output.
    raise NotImplementedError("strategy_value_summary not yet implemented")
