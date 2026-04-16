#!/usr/bin/env python3
"""
Pairwise policy benchmark for Module 5 checkpoints.

Runs head-to-head matches with alternating button and random combined stacks.
Reports BB/hand differential (preferred) and hand-win counts.
"""

from __future__ import annotations

import argparse
import itertools
import random
from pathlib import Path
from typing import Dict, List, Tuple

import module5_paths

module5_paths.ensure_module5_paths()

from action_mapping import legal_buckets, map_bucket_to_action
from full_game_engine.hu_hand import apply_action, legal_actions, new_hand
from rl_agent import RLPokerAgent
from rl_env import random_combined_stacks
from state_encoder import encode_from_hand_state


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Pairwise benchmark Module 5 policy checkpoints.")
    p.add_argument(
        "--policies",
        nargs="+",
        default=[
            str(module5_paths.MODULE_DIR / "checkpoints" / "optimal.pkl"),
            str(module5_paths.MODULE_DIR / "checkpoints" / "coverage.pkl"),
        ],
        help="Checkpoint paths (2+). Every pair is benchmarked.",
    )
    p.add_argument("--hands", type=int, default=10_000, help="Hands per pair")
    p.add_argument("--seed", type=int, default=1337, help="RNG seed")
    p.add_argument("--combined-bb-total", type=int, default=200)
    p.add_argument("--min-stack-bb", type=int, default=5)
    p.add_argument("--bb-chips", type=int, default=20)
    p.add_argument("--sb-chips", type=int, default=10)
    return p.parse_args()


def _pick_action(agent: RLPokerAgent, state) -> Dict[str, int]:
    enc = encode_from_hand_state(state, state.actor)
    lbs = legal_buckets(state)
    if not lbs:
        return legal_actions(state)[0]
    bucket = agent.select_action_masked(enc, lbs)
    return map_bucket_to_action(state, bucket)


def main() -> None:
    args = _parse_args()
    if len(args.policies) < 2:
        raise SystemExit("--policies requires at least 2 checkpoint paths")

    named_paths: List[Tuple[str, Path]] = []
    for p in args.policies:
        path = Path(p)
        if not path.exists():
            raise SystemExit(f"Checkpoint not found: {path}")
        named_paths.append((path.stem, path))

    agents: Dict[str, RLPokerAgent] = {}
    for name, path in named_paths:
        a = RLPokerAgent.load(path)
        a.epsilon = 0.0
        agents[name] = a

    rng = random.Random(args.seed)
    print(
        f"benchmark_hands_per_pair={args.hands} seed={args.seed} "
        f"combined_bb_total={args.combined_bb_total} min_stack_bb={args.min_stack_bb}"
    )
    print("")

    for (a_name, _), (b_name, _) in itertools.combinations(named_paths, 2):
        a = agents[a_name]
        b = agents[b_name]
        button = 0
        a_bb_total = 0.0
        b_bb_total = 0.0
        a_wins = 0
        b_wins = 0
        ties = 0

        for _ in range(args.hands):
            stacks = random_combined_stacks(
                args.combined_bb_total,
                args.bb_chips,
                rng,
                args.min_stack_bb,
                mode="uniform",
                extreme_prob=0.6,
            )
            state = new_hand(
                stacks,
                rng=rng,
                button=button,
                sb_chips=args.sb_chips,
                bb_chips=args.bb_chips,
            )
            start = list(state.stacks)

            while state.phase in {"preflop", "flop", "turn", "river"}:
                if not legal_actions(state):
                    break
                actor_agent = a if state.actor == 0 else b
                apply_action(state, _pick_action(actor_agent, state))
                if state.phase == "hand_over":
                    break

            d0 = (state.stacks[0] - start[0]) / float(args.bb_chips)
            d1 = (state.stacks[1] - start[1]) / float(args.bb_chips)
            a_bb_total += d0
            b_bb_total += d1
            if d0 > d1:
                a_wins += 1
            elif d1 > d0:
                b_wins += 1
            else:
                ties += 1
            button = 1 - button

        a_bbph = a_bb_total / args.hands
        b_bbph = b_bb_total / args.hands
        diff = a_bbph - b_bbph
        winner = a_name if diff > 0 else b_name if diff < 0 else "tie"

        print(f"PAIR {a_name} vs {b_name}")
        print(f"  winner_by_bb_per_hand: {winner}")
        print(f"  {a_name}_bb_per_hand: {a_bbph:.6f}")
        print(f"  {b_name}_bb_per_hand: {b_bbph:.6f}")
        print(f"  diff_bb_per_hand: {diff:.6f}")
        print(f"  hand_wins: {a_name}={a_wins}, {b_name}={b_wins}, ties={ties}")
        print("")


if __name__ == "__main__":
    main()

