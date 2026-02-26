"""
Monte Carlo simulator for pre-flop opening actions.

Runs many simulated trials (e.g., random opponent actions, hand runouts) to estimate
the value of an opening action. Does not use Module 2 heuristics or closed-form EV;
all value estimates come from simulation only.
"""

from typing import Tuple, Dict, Optional, List
import random


def run_trial(
    hand: str,
    action: str,
    bet_size: float,
    position: str,
    stack_sizes: Tuple[int, int],
    opponent_tendency: str,
    pot_size: float = 1.5,
    rng: Optional[random.Random] = None,
) -> float:
    """
    Run a single Monte Carlo trial: simulate one outcome (e.g., opponent fold/call/raise,
    or deal-out) for the given hand and opening action. Return the resulting payoff
    for this trial (e.g. in BB). No heuristics or Module 2 EV formulas—value from
    simulation only.

    Args:
        hand: Starting hand notation.
        action: "fold" or "open".
        bet_size: If action is "open", bet size in big blinds; ignored if "fold".
        position: "Button" or "Big Blind".
        stack_sizes: (your_stack, opponent_stack) in BB.
        opponent_tendency: Opponent tendency category (used to sample opponent behavior).
        pot_size: Current pot in BB.
        rng: Optional random number generator for reproducibility.

    Returns:
        Payoff for this single trial (e.g. in BB).
    """
    # TODO: Sample opponent response and/or runout from rng; compute payoff from
    # simulation only (no Module 2 EV).
    raise NotImplementedError("run_trial not yet implemented")


def run_simulation(
    hand: str,
    action: str,
    bet_size: float,
    position: str,
    stack_sizes: Tuple[int, int],
    opponent_tendency: str,
    num_trials: int = 1000,
    pot_size: float = 1.5,
    seed: Optional[int] = None,
) -> Dict:
    """
    Run num_trials Monte Carlo trials for (hand, action, bet_size) and return
    sample mean value, standard deviation, and confidence interval. All value
    from simulation; no Module 2 or EV formulas.

    Args:
        hand: Starting hand notation.
        action: "fold" or "open".
        bet_size: Opening bet size in BB (if action is "open").
        position: "Button" or "Big Blind".
        stack_sizes: (your_stack, opponent_stack) in BB.
        opponent_tendency: Opponent tendency.
        num_trials: Number of trials.
        pot_size: Pot size in BB.
        seed: Random seed for reproducibility.

    Returns:
        Dict with keys, e.g.:
        - "value_estimate": sample mean payoff
        - "std": sample standard deviation
        - "confidence_interval": (lower, upper) e.g. 95% CI
        - "num_trials": num_trials
    """
    # TODO: Call run_trial num_trials times; compute mean, std, CI.
    raise NotImplementedError("run_simulation not yet implemented")


def run_simulation_for_strategy(
    strategy: Dict[str, float],
    position: str,
    stack_sizes: Tuple[int, int],
    opponent_tendency: str,
    num_trials_per_hand: int = 500,
    hands: Optional[List[str]] = None,
    seed: Optional[int] = None,
) -> Dict:
    """
    Run Monte Carlo simulation for an entire strategy (hand -> opening bet size;
    fold can be represented as 0.0 or a sentinel). Optionally restrict to a list
    of hands; otherwise use strategy.keys(). Value from simulation only.

    Returns:
        Dict with overall value estimate, per-hand or per-range stats,
        and confidence intervals.
    """
    # TODO: For each hand in strategy, run run_simulation; aggregate results.
    raise NotImplementedError("run_simulation_for_strategy not yet implemented")
