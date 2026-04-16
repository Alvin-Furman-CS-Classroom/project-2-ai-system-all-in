"""
Training environment: wraps full_game_engine for RL (Module 5).

Train here; integrate with web_app / bot routing later.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple

import module5_paths

module5_paths.ensure_module5_paths()

from full_game_engine.hu_hand import HandState, apply_action, legal_actions, new_hand, random_legal_action

from action_mapping import DISCRETE_BUCKETS, map_bucket_to_action
from rl_agent import ActionBucket, StateKey
from state_encoder import encode_from_hand_state


@dataclass
class StepRecord:
    """One decision: state encoding, bucket, and acting seat."""

    enc: StateKey
    bucket: ActionBucket
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
    select_bucket: Callable[..., ActionBucket],
    rng: random.Random,
    stacks: List[int],
    button: int,
    sb_chips: int = 10,
    bb_chips: int = 20,
    random_legal_seat: Optional[int] = None,
    strict_buckets: bool = True,
) -> EpisodeResult:
    """
    Play one hand of self-play.

    ``select_bucket(state, encoded_state, hero) -> bucket str`` is used for the learning
    policy. If ``random_legal_seat`` is 0 or 1, that seat instead picks a uniform random
    legal engine action (no discrete bucket); those decisions are **not** recorded in
    ``steps`` so training updates apply only to the RL seat.

    If ``strict_buckets`` is True (default), ``select_bucket`` must return a label in
    ``DISCRETE_BUCKETS``; otherwise :class:`ValueError` is raised. If False, an invalid
    label is replaced with a random bucket (legacy tolerance for noisy policies).
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
                if strict_buckets:
                    raise ValueError(
                        f"select_bucket returned invalid bucket {bucket!r}; "
                        f"expected one of {DISCRETE_BUCKETS}"
                    )
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


# ``extreme_mix`` samples from the low or high *quarter* of valid stack splits (see README).
_STACK_SPLIT_QUARTERS = 4


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
        quarter = max(1, span // _STACK_SPLIT_QUARTERS)
        if rng.random() < 0.5:
            s0 = rng.randint(lo, min(lo + quarter, hi))
        else:
            s0 = rng.randint(max(lo, hi - quarter), hi)
    else:
        s0 = rng.randint(lo, hi)
    return [s0, total_chips - s0]
