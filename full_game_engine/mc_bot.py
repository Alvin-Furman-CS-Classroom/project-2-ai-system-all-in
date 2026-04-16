"""
Bot policy using Module 3 Monte Carlo rollouts (not MCTS — there is no tree search).

For each legal preflop action, estimates EV via ``run_simulation`` and picks the best.
Falls back to random legal action if Module 3 cannot be imported or on error.
"""

from __future__ import annotations

import random
from pathlib import Path
from typing import Any, Dict

from engine_mc_adapter_utils import hole_cards_to_mc_hand_generic, mc_bot_action_generic
from full_game_engine.cards import RANKS, SUITS, Card
from full_game_engine.hu_hand import HandState, legal_actions, random_legal_action
import project_paths

_M3 = Path(__file__).resolve().parent.parent / "Module 3"
project_paths.ensure_paths((_M3,))

try:
    from monte_carlo_simulator import run_simulation  # type: ignore
except ImportError:  # pragma: no cover
    run_simulation = None  # type: ignore

# Default trials per action (keep low for web latency)
DEFAULT_TRIALS_PER_ACTION = 28
OPPONENT_TENDENCY = "Unknown"


def hole_cards_to_mc_hand(c0: Card, c1: Card) -> str:
    """Compact hand label for Module 3 (e.g. ``AKs``, ``72o``, ``AA``)."""
    return hole_cards_to_mc_hand_generic(c0, c1, rank_lookup=RANKS, suit_lookup=SUITS)


def mc_bot_action(
    state: HandState,
    rng: random.Random,
    *,
    num_trials_per_action: int = DEFAULT_TRIALS_PER_ACTION,
) -> Dict[str, Any]:
    """
    Choose a legal action with highest estimated EV from Module 3 Monte Carlo rollouts.
    Ties broken uniformly at random.
    """
    if run_simulation is None:
        return random_legal_action(state, rng)

    acts = legal_actions(state)
    p = state.actor
    c0, c1 = state.hole_cards[p]
    hand_str = hole_cards_to_mc_hand(c0, c1)
    return mc_bot_action_generic(
        state=state,
        rng=rng,
        legal_actions=acts,
        run_simulation=run_simulation,
        hand_str=hand_str,
        num_trials_per_action=num_trials_per_action,
        opponent_tendency=OPPONENT_TENDENCY,
    )


def mc_or_random_action(
    state: HandState,
    rng: random.Random,
    *,
    use_mc: bool = True,
    num_trials_per_action: int = DEFAULT_TRIALS_PER_ACTION,
) -> Dict[str, Any]:
    """Use Monte Carlo bot when possible; otherwise random legal."""
    if not use_mc or run_simulation is None:
        return random_legal_action(state, rng)
    try:
        return mc_bot_action(state, rng, num_trials_per_action=num_trials_per_action)
    except (RuntimeError, ValueError, TypeError, KeyError):
        return random_legal_action(state, rng)

