"""
Monte Carlo optimization of opening actions.

Uses Monte Carlo simulation to find optimal opening actions (fold or open to X BB)
per hand or range. Candidate actions are evaluated by running many simulated outcomes 
and choosing the action that maximizes simulated value.
"""

from __future__ import annotations

from typing import Dict, Tuple, Optional, List, Any

from monte_carlo_simulator import run_simulation
from strategy_evaluator import evaluate_strategy


DEFAULT_HANDS: List[str] = ["AA", "KK", "QQ", "JJ", "TT", "AKs", "AQs", "AJs", "KQs", "72o"]
DEFAULT_BET_SIZES: List[float] = [2.0, 2.5, 3.0, 4.0, 5.0]


def optimize_opening_actions(
    position: str,
    stack_sizes: Tuple[int, int],
    opponent_tendency: str,
    knowledge_base_from_module1: Optional[Any] = None,
    hands: Optional[List[str]] = None,
    candidate_bet_sizes: Optional[List[float]] = None,
    num_simulations: int = 1000,
    seed: Optional[int] = None,
) -> Dict:
    """
    Compute optimal opening actions using Monte Carlo simulation.

    For each hand (or each hand in hands), simulate outcomes for "fold" and for
    "open to X" for each candidate bet size; choose the action (fold or open to X)
    that maximizes simulated value.

    Args:
        position: "Button" or "Big Blind".
        stack_sizes: (your_stack, opponent_stack) in BB.
        opponent_tendency: Opponent tendency category.
        knowledge_base_from_module1: Optional Module 1 output for playability (e.g.
            only consider hands that are playable).
        hands: List of hands to optimize; if None, use a default set of hands.
        candidate_bet_sizes: Opening bet sizes to consider (in BB); if None, use
            a default set (e.g. 2, 2.5, 3, 4, 5).
        num_simulations: Number of Monte Carlo trials per (hand, action) pair.
        seed: Random seed.

    Returns:
        Dict with:
        - "optimized_strategy": dict hand -> recommended opening action encoded as
            a float bet size in BB (0.0 = fold).
        - "expected_value": Estimated value of the strategy (from simulation).
        - "confidence_interval": (lower, upper) for strategy value.
        - "hand_recommendations": list of (hand, action, value_estimate).
    """
    rng_seed = seed
    hands_to_use = list(hands) if hands is not None else list(DEFAULT_HANDS)
    bet_sizes = list(candidate_bet_sizes) if candidate_bet_sizes is not None else list(DEFAULT_BET_SIZES)

    optimized_strategy: Dict[str, float] = {}
    hand_recommendations: List[Dict[str, Any]] = []

    for hand in hands_to_use:
        # Optional: honor Module 1 playability if provided
        if knowledge_base_from_module1 is not None:
            # Expecting a dict-like with per-hand playability, or a single boolean.
            # To keep this generic, if a mapping is provided and this hand is marked
            # unplayable, we always fold.
            playable_map = getattr(knowledge_base_from_module1, "get", None)
            if callable(playable_map):
                playable = knowledge_base_from_module1.get(hand, True)
            else:
                playable = bool(knowledge_base_from_module1)
            if not playable:
                optimized_strategy[hand] = 0.0
                hand_recommendations.append(
                    {"hand": hand, "action": "fold", "bet_size": 0.0, "value_estimate": 0.0}
                )
                continue

        # Evaluate fold (baseline 0.0)
        best_action = "fold"
        best_bet_size = 0.0
        best_value = 0.0

        # Evaluate each candidate bet size via Monte Carlo
        for bet in bet_sizes:
            result = run_simulation(
                hand=hand,
                action="open",
                bet_size=bet,
                position=position,
                stack_sizes=stack_sizes,
                opponent_tendency=opponent_tendency,
                num_trials=num_simulations,
                pot_size=1.5,
                seed=rng_seed,
            )
            value_estimate = result["value_estimate"]
            if value_estimate > best_value:
                best_value = value_estimate
                best_action = "open"
                best_bet_size = bet

        optimized_strategy[hand] = 0.0 if best_action == "fold" else best_bet_size
        hand_recommendations.append(
            {
                "hand": hand,
                "action": best_action,
                "bet_size": best_bet_size,
                "value_estimate": best_value,
            }
        )

    # Evaluate the overall strategy using Monte Carlo
    strategy_eval = evaluate_strategy(
        strategy=optimized_strategy,
        position=position,
        stack_sizes=stack_sizes,
        opponent_tendency=opponent_tendency,
        num_trials=num_simulations,
        seed=seed,
    )

    return {
        "optimized_strategy": optimized_strategy,
        "expected_value": strategy_eval["expected_value"],
        "confidence_interval": strategy_eval["confidence_interval"],
        "hand_recommendations": hand_recommendations,
    }


def get_opening_strategy_for_module4(
    position: str,
    stack_sizes: Tuple[int, int],
    opponent_tendency: str,
    num_simulations: int = 500,
    seed: Optional[int] = None,
) -> Dict:
    """
    Produce the output format expected by Module 4: optimal opening action
    strategy (from Monte Carlo only), expected value, and confidence intervals.
    No Module 2 dependency.

    Returns:
        Dict with optimized opening strategy, expected value,
        confidence intervals, and optional list of hands and actions.
    """
    result = optimize_opening_actions(
        position=position,
        stack_sizes=stack_sizes,
        opponent_tendency=opponent_tendency,
        hands=None,
        candidate_bet_sizes=None,
        num_simulations=num_simulations,
        seed=seed,
    )

    return result
