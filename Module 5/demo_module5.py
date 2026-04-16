#!/usr/bin/env python3
"""
Demo: Module 5 RL agent training on full_game_engine (self-play).
"""

from __future__ import annotations

import random

import module5_paths

module5_paths.ensure_module5_paths()

from action_mapping import DISCRETE_BUCKETS
from rl_agent import RLPokerAgent
from trainer import evaluate_bb_per_hand, train_self_play


def main() -> None:
    rng = random.Random(42)
    agent = RLPokerAgent(
        actions=list(DISCRETE_BUCKETS),
        alpha=0.1,
        gamma=0.95,
        epsilon=0.2,
    )

    train_episodes = 400
    print("Training self-play on full_game_engine (Monte Carlo + masked exploration)...")
    train_self_play(
        agent,
        episodes=train_episodes,
        rng=rng,
        starting_bb_each=100,
        bb_chips=20,
        sb_chips=10,
        use_masked_exploration=True,
        use_monte_carlo=True,
        randomize_stacks=True,
        combined_bb_total=200,
        min_stack_bb_each=5,
    )

    eval_n = 200
    ev = evaluate_bb_per_hand(
        agent,
        episodes=eval_n,
        rng=random.Random(123),
        randomize_stacks=True,
        combined_bb_total=200,
        min_stack_bb_each=5,
    )
    print(f"Greedy eval over {eval_n} hands (BB/hand, stack change after blinds):")
    print(f"  seat 0: {ev.mean_seat0:.4f}")
    print(f"  seat 1: {ev.mean_seat1:.4f}")
    print(f"  seat0 - seat1 (symmetric ~0): {ev.mean_seat_diff:.4f}")
    print(f"  (seat0+seat1)/2 (not 0-sum; ~half avg pot BB): {ev.mean_combined:.4f}")
    print("Done.")


if __name__ == "__main__":
    main()
