"""
Training environment: wraps full_game_engine for RL (Module 5).

Train here; integrate with web_app / bot routing later.
"""

from __future__ import annotations

import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

_M5 = Path(__file__).resolve().parent
_ROOT = _M5.parent
for _p in (_ROOT, _M5):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from full_game_engine.hu_hand import HandState, apply_action, legal_actions, new_hand

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
    select_bucket,
    rng: random.Random,
    stacks: List[int],
    button: int,
    sb_chips: int = 10,
    bb_chips: int = 20,
) -> EpisodeResult:
    """
    Play one hand of self-play: both seats use select_bucket(state, encoded_state, hero).

    select_bucket signature: (HandState, encoded_tuple, hero:int) -> bucket str
    """
    state = new_hand(list(stacks), rng=rng, button=button, sb_chips=sb_chips, bb_chips=bb_chips)
    start_chips = list(state.stacks)

    steps: List[StepRecord] = []

    while is_betting(state):
        if not legal_actions(state):
            break
        hero = state.actor
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
) -> List[int]:
    """
    Randomly split ``total_bb`` big blinds worth of chips between both players.

    Total chips = ``total_bb * bb_chips`` (exact). Each player gets at least
    ``min_each_bb * bb_chips`` chips so both can post blinds and have room to act.

    Use this during training to cover deep-stack vs short-stack asymmetry while keeping
    total money in play fixed (e.g. 200 BB combined for human vs bot sessions).
    """
    if total_bb < 2 * min_each_bb:
        raise ValueError(f"total_bb ({total_bb}) must be >= 2 * min_each_bb ({2 * min_each_bb})")
    total_chips = total_bb * bb_chips
    min_chips = min_each_bb * bb_chips
    lo = min_chips
    hi = total_chips - min_chips
    s0 = rng.randint(lo, hi)
    s1 = total_chips - s0
    return [s0, s1]
