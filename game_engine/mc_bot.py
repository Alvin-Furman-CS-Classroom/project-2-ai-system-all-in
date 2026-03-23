"""
Bot policy using Module 3 Monte Carlo rollouts (not MCTS — there is no tree search).

For each legal preflop action, estimates EV via ``run_simulation`` and picks the best.
Falls back to random legal action if Module 3 cannot be imported or on error.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

from game_engine.cards import RANKS, SUITS, Card
from game_engine.hu_preflop import HandState, legal_actions, random_legal_action

_M3 = Path(__file__).resolve().parent.parent / "Module 3"
if str(_M3) not in sys.path:
    sys.path.insert(0, str(_M3))

try:
    from monte_carlo_simulator import run_simulation  # type: ignore
except ImportError:  # pragma: no cover
    run_simulation = None  # type: ignore

# Default trials per action (keep low for web latency)
DEFAULT_TRIALS_PER_ACTION = 28
OPPONENT_TENDENCY = "Unknown"


def hole_cards_to_mc_hand(c0: Card, c1: Card) -> str:
    """Compact hand label for Module 3 (e.g. ``AKs``, ``72o``, ``AA``)."""
    r0, r1 = RANKS[c0.rank], RANKS[c1.rank]
    suited = SUITS[c0.suit] == SUITS[c1.suit]
    order = "23456789TJQKA"
    if r0 == r1:
        return f"{r0}{r1}"
    if order.index(r0) >= order.index(r1):
        hi, lo = r0, r1
    else:
        hi, lo = r1, r0
    return f"{hi}{lo}{'s' if suited else 'o'}"


def _stacks_bb_bot_view(state: HandState, bot_seat: int) -> Tuple[float, float]:
    bb = float(state.bb_chips)
    s0 = state.stacks[0] / bb
    s1 = state.stacks[1] / bb
    if bot_seat == 1:
        return (s1, s0)
    return (s0, s1)


def _position_label(state: HandState, bot_seat: int) -> str:
    return "Button" if state.button == bot_seat else "Big Blind"


def _estimate_action_ev(
    state: HandState,
    bot_seat: int,
    hand_str: str,
    action: Dict[str, Any],
    num_trials: int,
    seed: int,
) -> float:
    """Map a legal engine action to Module 3 ``run_simulation`` and return mean value."""
    bb = float(state.bb_chips)
    stacks_bb = _stacks_bb_bot_view(state, bot_seat)
    pos = _position_label(state, bot_seat)
    pot_bb = max(state.pot / bb, 0.5)

    kind = action["kind"]
    if kind == "fold":
        return 0.0

    if kind == "check":
        # No chips to call: approximate as limp / minimum pressure spot
        res = run_simulation(
            hand=hand_str,
            action="open",
            bet_size=1.0,
            position=pos,
            stack_sizes=stacks_bb,
            opponent_tendency=OPPONENT_TENDENCY,
            num_trials=num_trials,
            pot_size=pot_bb,
            seed=seed,
        )
        return float(res["value_estimate"])

    if kind == "call":
        tc = float(action["amount"])
        bet_bb = max(tc / bb, 0.5)
        res = run_simulation(
            hand=hand_str,
            action="open",
            bet_size=bet_bb,
            position=pos,
            stack_sizes=stacks_bb,
            opponent_tendency=OPPONENT_TENDENCY,
            num_trials=num_trials,
            pot_size=pot_bb,
            seed=seed,
        )
        return float(res["value_estimate"])

    if kind == "raise_to":
        total = float(action["total"])
        bet_bb = max(total / bb, 0.5)
        res = run_simulation(
            hand=hand_str,
            action="open",
            bet_size=bet_bb,
            position=pos,
            stack_sizes=stacks_bb,
            opponent_tendency=OPPONENT_TENDENCY,
            num_trials=num_trials,
            pot_size=pot_bb,
            seed=seed,
        )
        return float(res["value_estimate"])

    return 0.0


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

    acts: List[Dict[str, Any]] = legal_actions(state)
    if not acts:
        raise ValueError("No legal actions")

    p = state.actor
    c0, c1 = state.hole_cards[p]
    hand_str = hole_cards_to_mc_hand(c0, c1)

    evs: List[float] = []
    for act in acts:
        try:
            evs.append(
                _estimate_action_ev(
                    state,
                    p,
                    hand_str,
                    act,
                    num_trials_per_action,
                    rng.randint(0, 2**31 - 1),
                )
            )
        except Exception:
            evs.append(float("-inf"))

    best_ev = max(evs)
    best_idx = [i for i, v in enumerate(evs) if v >= best_ev - 1e-9]
    pick = rng.choice(best_idx)
    return acts[pick]


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
    except Exception:
        return random_legal_action(state, rng)
