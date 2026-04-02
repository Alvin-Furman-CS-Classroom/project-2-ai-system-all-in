"""
Training environment: wraps full_game_engine for RL (Module 5).

Train here; integrate with web_app / bot routing later.
"""

from __future__ import annotations

import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional, Tuple

_M5 = Path(__file__).resolve().parent
_ROOT = _M5.parent
for _p in (_ROOT, _M5):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from full_game_engine.hu_hand import HandState, apply_action, legal_actions, new_hand, random_legal_action

from action_mapping import DISCRETE_BUCKETS, map_bucket_to_action
from state_encoder import encode_from_hand_state


@dataclass
class StepRecord:
    """One decision: state encoding, bucket, and acting seat."""

    enc: Tuple
    bucket: str
    hero: int


@dataclass
class EpisodeResult:
    steps: List[StepRecord]
    stacks_delta_bb: Tuple[float, float]
    """Net BB change vs hand start for seat 0 and 1 (same as R_p for Monte Carlo)."""
    button: int


def is_betting(state: HandState) -> bool:
    return state.phase in {"preflop", "flop", "turn", "river"}


def run_episode(
    select_bucket: Callable[..., str],
    rng: random.Random,
    stacks: List[int],
    button: int,
    sb_chips: int = 10,
    bb_chips: int = 20,
    random_legal_seat: Optional[int] = None,
) -> EpisodeResult:
    """
    Play one hand of self-play.

    ``select_bucket(state, encoded_state, hero) -> bucket str`` is used for the learning
    policy. If ``random_legal_seat`` is 0 or 1, that seat instead picks a uniform random
    legal engine action (no discrete bucket); those decisions are **not** recorded in
    ``steps`` so training updates apply only to the RL seat.
    """
    if random_legal_seat is not None and random_legal_seat not in (0, 1):
        raise ValueError("random_legal_seat must be None, 0, or 1")

    state = new_hand(list(stacks), rng=rng, button=button, sb_chips=sb_chips, bb_chips=bb_chips)
    start_chips = list(state.stacks)

    steps: List[StepRecord] = []

    while is_betting(state):
        if not legal_actions(state):
            break
        hero = state.actor
        if hero == random_legal_seat:
            apply_action(state, random_legal_action(state, rng))
        else:
            enc = encode_from_hand_state(state, hero)
            bucket = select_bucket(state, enc, hero)
            if bucket not in DISCRETE_BUCKETS:
                bucket = rng.choice(DISCRETE_BUCKETS)
            action = map_bucket_to_action(state, bucket)
            steps.append(StepRecord(enc=enc, bucket=bucket, hero=hero))
            apply_action(state, action)

        if state.phase == "hand_over":
            break

    bb_f = float(bb_chips)
    d0 = (state.stacks[0] - start_chips[0]) / bb_f
    d1 = (state.stacks[1] - start_chips[1]) / bb_f
    return EpisodeResult(steps=steps, stacks_delta_bb=(d0, d1), button=button)


def new_starting_stacks(starting_bb_each: int, bb_chips: int) -> List[int]:
    return [starting_bb_each * bb_chips, starting_bb_each * bb_chips]


def random_combined_stacks(
    total_bb: int,
    bb_chips: int,
    rng: random.Random,
    min_each_bb: int = 5,
    mode: str = "uniform",
    extreme_prob: float = 0.6,
) -> List[int]:
    """
    Randomly split ``total_bb`` big blinds worth of chips between both players.

    Total chips = ``total_bb * bb_chips`` (exact). Each player gets at least
    ``min_each_bb * bb_chips`` chips so both can post blinds and have room to act.

    ``mode``:
    - ``uniform``: uniform over valid splits.
    - ``extreme_mix``: with probability ``extreme_prob``, sample from the low or high
      quarter of the range (short vs deep stack skew); otherwise uniform.

    Use this during training to cover deep-stack vs short-stack asymmetry while keeping
    total money in play fixed (e.g. 200 BB combined for human vs bot sessions).
    """
    if total_bb < 2 * min_each_bb:
        raise ValueError(f"total_bb ({total_bb}) must be >= 2 * min_each_bb ({2 * min_each_bb})")
    total_chips = total_bb * bb_chips
    min_chips = min_each_bb * bb_chips
    lo = min_chips
    hi = total_chips - min_chips
    span = hi - lo
    if span < 0:
        raise ValueError("invalid stack range")
    if mode != "extreme_mix" or span == 0:
        s0 = rng.randint(lo, hi)
        return [s0, total_chips - s0]

    if rng.random() < extreme_prob:
        quarter = max(1, span // 4)
        if rng.random() < 0.5:
            s0 = rng.randint(lo, min(lo + quarter, hi))
        else:
            s0 = rng.randint(max(lo, hi - quarter), hi)
    else:
        s0 = rng.randint(lo, hi)
    return [s0, total_chips - s0]
