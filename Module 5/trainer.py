"""
Training utilities for Module 5: self-play on full_game_engine.
"""

from __future__ import annotations

import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

_M5 = Path(__file__).resolve().parent
_ROOT = _M5.parent
for _p in (_ROOT, _M5):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from action_mapping import legal_buckets
from rl_agent import RLPokerAgent
from rl_env import new_starting_stacks, random_combined_stacks, run_episode

Transition = Tuple[object, str, float, object, bool]


@dataclass
class EvalBBPerHand:
    """
    Per-hand stack deltas are measured **after blinds are posted**.

    In that accounting, ``mean_seat0 + mean_seat1`` is **not** 0: the two deltas sum to
    about the initial pot in BB (money moving from “middle” into stacks). So
    ``mean_combined`` is **not** a zero-sum sanity check.

    For symmetric self-play with alternating buttons, ``mean_seat0 - mean_seat1`` should
    trend to **0** (each seat’s EV vs the other).
    """

    mean_seat0: float
    mean_seat1: float
    mean_combined: float
    mean_seat_diff: float


def train_from_transitions(agent: RLPokerAgent, transitions: Iterable[Transition]) -> None:
    """Offline batch TD update from stored transitions (optional)."""
    for s, a, r, s2, done in transitions:
        agent.update(s, a, r, s2, done)


def epsilon_for_episode(
    ep: int,
    total_episodes: int,
    epsilon_start: float = 0.2,
    epsilon_end: float = 0.02,
    decay_fraction: float = 0.7,
) -> float:
    decay_n = max(1, int(total_episodes * decay_fraction))
    if ep >= decay_n:
        return epsilon_end
    t = ep / max(decay_n - 1, 1)
    return epsilon_start + (epsilon_end - epsilon_start) * t


def train_self_play(
    agent: RLPokerAgent,
    episodes: int,
    rng: Optional[random.Random] = None,
    starting_bb_each: int = 100,
    bb_chips: int = 20,
    sb_chips: int = 10,
    epsilon_start: float = 0.2,
    epsilon_end: float = 0.02,
    decay_fraction: float = 0.7,
    use_masked_exploration: bool = True,
    use_monte_carlo: bool = True,
    initial_button: int = 0,
    episode_index_start: int = 0,
    epsilon_schedule_total: Optional[int] = None,
    randomize_stacks: bool = False,
    combined_bb_total: int = 200,
    min_stack_bb_each: int = 5,
) -> Tuple[List[float], int]:
    """
    Run self-play episodes; both seats share the same policy.

    **Monte Carlo (default):** each ``(s, a)`` by seat *p* is updated toward the hand's
    net BB return *G* for *p* (same *G* for every step seat *p* took in that hand).

    **TD alternative:** one-step Q-learning with ``r=0`` until the last transition; the
    last transition uses the full-hand net BB for the acting player (coarse credit).

    **Masked exploration (default):** epsilon-greedy only over `legal_buckets(state)`.

    Returns ``(per_episode_seat0_bb, final_button)`` for checkpointed / resumed runs.

    ``epsilon_schedule_total`` is the horizon over which epsilon decays (first ``decay_fraction``
    of that). If ``None``, it defaults to ``episodes`` (single-call behavior). Use a large
    fixed value plus ``episode_index_start`` when splitting one long run across chunks.

    **Stack randomization:** if ``randomize_stacks`` is True, each hand samples a random split of
    ``combined_bb_total`` BB between the two players (see ``random_combined_stacks``). Otherwise
    both start with ``starting_bb_each`` BB (legacy behavior).
    """
    rng = rng or random.Random()
    seat0_bb: List[float] = []
    button = initial_button & 1
    sched = epsilon_schedule_total if epsilon_schedule_total is not None else episodes

    for ep in range(episodes):
        global_ep = episode_index_start + ep
        agent.epsilon = epsilon_for_episode(global_ep, sched, epsilon_start, epsilon_end, decay_fraction)
        if randomize_stacks:
            stacks = random_combined_stacks(combined_bb_total, bb_chips, rng, min_stack_bb_each)
        else:
            stacks = new_starting_stacks(starting_bb_each, bb_chips)

        def select(state, enc, hero: int) -> str:
            if use_masked_exploration:
                return agent.select_action_masked(enc, legal_buckets(state))
            return agent.select_action(enc)

        res = run_episode(select, rng, stacks, button, sb_chips=sb_chips, bb_chips=bb_chips)

        r0, r1 = res.stacks_delta_bb
        if use_monte_carlo:
            for step in res.steps:
                g = r0 if step.hero == 0 else r1
                agent.update_monte_carlo(step.enc, step.bucket, g)
        else:
            for i, step in enumerate(res.steps):
                g = r0 if step.hero == 0 else r1
                is_last = i == len(res.steps) - 1
                if is_last:
                    agent.update(step.enc, step.bucket, g, step.enc, True)
                else:
                    nxt = res.steps[i + 1].enc
                    agent.update(step.enc, step.bucket, 0.0, nxt, False)

        seat0_bb.append(r0)
        button = 1 - button

    return seat0_bb, button


def evaluate_bb_per_hand(
    agent: RLPokerAgent,
    episodes: int,
    rng: Optional[random.Random] = None,
    starting_bb_each: int = 100,
    bb_chips: int = 20,
    sb_chips: int = 10,
    use_masked_exploration: bool = True,
    randomize_stacks: bool = False,
    combined_bb_total: int = 200,
    min_stack_bb_each: int = 5,
) -> EvalBBPerHand:
    """
    Greedy play (epsilon=0): mean BB/hand per seat, combined average, and seat0−seat1.

    Use ``mean_seat_diff`` (≈ 0 long-run) for symmetry; ``mean_combined`` is not a zero-sum
    check (see README). Docstring on ``EvalBBPerHand`` explains the accounting.
    """
    rng = rng or random.Random()
    old_eps = agent.epsilon
    agent.epsilon = 0.0
    button = 0
    total0 = 0.0
    total1 = 0.0

    for _ in range(episodes):
        if randomize_stacks:
            stacks = random_combined_stacks(combined_bb_total, bb_chips, rng, min_stack_bb_each)
        else:
            stacks = new_starting_stacks(starting_bb_each, bb_chips)

        def select(state, enc, hero: int) -> str:
            if use_masked_exploration:
                return agent.select_action_masked(enc, legal_buckets(state))
            return agent.select_action(enc)

        res = run_episode(select, rng, stacks, button, sb_chips=sb_chips, bb_chips=bb_chips)
        d0, d1 = res.stacks_delta_bb
        total0 += d0
        total1 += d1
        button = 1 - button

    agent.epsilon = old_eps
    n = max(episodes, 1)
    m0 = total0 / n
    m1 = total1 / n
    return EvalBBPerHand(
        mean_seat0=m0,
        mean_seat1=m1,
        mean_combined=(m0 + m1) / 2.0,
        mean_seat_diff=m0 - m1,
    )
