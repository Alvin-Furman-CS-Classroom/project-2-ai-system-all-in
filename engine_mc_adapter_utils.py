"""
Shared Monte Carlo adapter helpers used by both engine stacks.
"""

from __future__ import annotations

import random
from typing import Any, Callable, Dict, List, Sequence, Tuple

Action = Dict[str, Any]


def hole_cards_to_mc_hand_generic(
    c0: Any,
    c1: Any,
    *,
    rank_lookup: Dict[int, str],
    suit_lookup: Dict[int, str],
) -> str:
    """Compact hand label for Module 3 (e.g. ``AKs``, ``72o``, ``AA``)."""
    r0, r1 = rank_lookup[c0.rank], rank_lookup[c1.rank]
    suited = suit_lookup[c0.suit] == suit_lookup[c1.suit]
    order = "23456789TJQKA"
    if r0 == r1:
        return f"{r0}{r1}"
    hi, lo = (r0, r1) if order.index(r0) >= order.index(r1) else (r1, r0)
    return f"{hi}{lo}{'s' if suited else 'o'}"


def _stacks_bb_bot_view(state: Any, bot_seat: int) -> Tuple[float, float]:
    bb = float(state.bb_chips)
    s0 = state.stacks[0] / bb
    s1 = state.stacks[1] / bb
    return (s1, s0) if bot_seat == 1 else (s0, s1)


def _position_label(state: Any, bot_seat: int) -> str:
    return "Button" if state.button == bot_seat else "Big Blind"


def _bet_size_bb_for_action(action: Action, bb: float) -> float:
    kind = action["kind"]
    if kind == "check":
        return 1.0
    if kind == "call":
        return max(float(action["amount"]) / bb, 0.5)
    if kind == "raise_to":
        return max(float(action["total"]) / bb, 0.5)
    return 0.0


def _estimate_action_ev(
    *,
    run_simulation: Callable[..., Dict[str, Any]],
    state: Any,
    bot_seat: int,
    hand_str: str,
    action: Action,
    num_trials: int,
    seed: int,
    opponent_tendency: str,
) -> float:
    kind = action["kind"]
    if kind == "fold":
        return 0.0
    bb = float(state.bb_chips)
    c0, c1 = state.hole_cards[bot_seat]
    res = run_simulation(
        hand=hand_str,
        action="open",
        bet_size=_bet_size_bb_for_action(action, bb),
        position=_position_label(state, bot_seat),
        stack_sizes=_stacks_bb_bot_view(state, bot_seat),
        opponent_tendency=opponent_tendency,
        num_trials=num_trials,
        pot_size=max(state.pot / bb, 0.5),
        seed=seed,
        hero_hole=(c0, c1),
        board=list(state.board),
    )
    return float(res["value_estimate"])


def mc_bot_action_generic(
    *,
    state: Any,
    rng: random.Random,
    legal_actions: Sequence[Action],
    run_simulation: Callable[..., Dict[str, Any]],
    hand_str: str,
    num_trials_per_action: int,
    opponent_tendency: str,
) -> Action:
    """Choose a legal action with highest estimated EV from Module 3 rollouts."""
    if not legal_actions:
        raise ValueError("No legal actions")
    seat = state.actor
    evs: List[float] = []
    for act in legal_actions:
        try:
            evs.append(
                _estimate_action_ev(
                    run_simulation=run_simulation,
                    state=state,
                    bot_seat=seat,
                    hand_str=hand_str,
                    action=act,
                    num_trials=num_trials_per_action,
                    seed=rng.randint(0, 2**31 - 1),
                    opponent_tendency=opponent_tendency,
                )
            )
        except (RuntimeError, ValueError, TypeError, KeyError):
            evs.append(float("-inf"))
    best_ev = max(evs)
    best_idx = [i for i, v in enumerate(evs) if v >= best_ev - 1e-9]
    return legal_actions[rng.choice(best_idx)]
