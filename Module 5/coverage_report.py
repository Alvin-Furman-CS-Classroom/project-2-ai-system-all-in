#!/usr/bin/env python3
"""
Coverage report for Module 5 tabular RL checkpoints.

Uses **sampled reachable** encodings from legal engine trajectories (not a Cartesian
theoretical upper bound). Reports overlap between the checkpoint Q-table keys and
that sample.

Usage:
  python3 "Module 5/coverage_report.py" --checkpoint "Module 5/checkpoints/my_policy.pkl"
  python3 "Module 5/coverage_report.py" --checkpoint policy.pkl --save-missing-states gaps.pkl
"""

from __future__ import annotations

import argparse
import pickle
import random
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Set, Tuple

_M5 = Path(__file__).resolve().parent
_ROOT = _M5.parent
for _p in (_ROOT, _M5):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from full_game_engine.hu_hand import apply_action, legal_actions, new_hand
from rl_agent import RLPokerAgent
from state_encoder import encode_from_hand_state


def _bucket_linear(x: float, edges: Tuple[float, ...]) -> int:
    for i, e in enumerate(edges):
        if x < e:
            return i
    return len(edges)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Report checkpoint coverage vs sampled reachable encodings (Module 5).",
    )
    p.add_argument(
        "--checkpoint",
        type=Path,
        default=_M5 / "checkpoints" / "my_policy.pkl",
        help="Path to Module 5 policy checkpoint",
    )
    p.add_argument(
        "--head",
        type=int,
        default=8,
        help="Rows to print for distributions",
    )
    p.add_argument(
        "--combined-bb-total",
        type=float,
        default=200.0,
        help="Combined BB at hand start for reachable sampling (random split before blinds)",
    )
    p.add_argument(
        "--sb-bb",
        type=float,
        default=0.5,
        help="Small blind size in BB for reachable sampling",
    )
    p.add_argument(
        "--bb-bb",
        type=float,
        default=1.0,
        help="Big blind size in BB for reachable sampling",
    )
    p.add_argument(
        "--reachable-sim-episodes",
        type=int,
        default=20_000,
        help="Number of simulated hands to build the reachable encoding sample (must be > 0)",
    )
    p.add_argument(
        "--reachable-sim-seed",
        type=int,
        default=42,
        help="Seed for reachable-state simulation",
    )
    p.add_argument(
        "--save-missing-states",
        type=Path,
        default=None,
        metavar="PATH",
        help="Write pickle of encodings seen in sim but absent from Q (sim_reachable - policy keys)",
    )
    return p.parse_args()


def _safe_get_street(state: Tuple[Any, ...]) -> str:
    if len(state) > 2 and isinstance(state[0], str) and state[0].startswith("v"):
        if isinstance(state[2], str):
            return state[2]
    if len(state) > 1 and isinstance(state[1], str):
        return state[1]
    return "unknown"


def _safe_get_hand_kind(state: Tuple[Any, ...]) -> str:
    if not state:
        return "unknown"
    hand = state[1] if (len(state) > 1 and isinstance(state[0], str) and state[0].startswith("v")) else state[0]
    if isinstance(hand, tuple) and hand:
        return str(hand[0])
    return "unknown"


def _encode_legacy_from_hand_state(state: Any, hero: int) -> Tuple[Any, ...]:
    """
    Legacy encoding shape: (hand, street, position, sb, ob, pb, tb, bf)
    (must match keys in legacy checkpoints).
    """
    bb = float(state.bb_chips)
    c0, c1 = state.hole_cards[hero]
    r0, r1 = c0.rank, c1.rank
    if r0 == r1:
        hand = ("pair", _bucket_linear(float(r0), (5.0, 8.0, 11.0)))
    else:
        hi, lo = max(r0, r1), min(r0, r1)
        suited = 1 if c0.suit == c1.suit else 0
        hand = ("np", _bucket_linear(float(hi), (6.0, 8.0, 11.0)), _bucket_linear(float(lo), (5.0, 8.0)), suited)

    position = 1 if hero == state.button else 0
    my_stack_bb = state.stacks[hero] / bb
    opp_stack_bb = state.stacks[1 - hero] / bb
    pot_bb = state.pot / bb
    tc_bb = state.to_call(hero) / bb

    sb = _bucket_linear(my_stack_bb, (15.0, 40.0, 100.0))
    ob = _bucket_linear(opp_stack_bb, (15.0, 40.0, 100.0))
    pb = _bucket_linear(pot_bb, (2.0, 8.0, 24.0))
    tb = _bucket_linear(tc_bb, (1.0, 3.0, 8.0))

    board = tuple(state.board)
    n = len(board)
    if n == 0:
        bf = (0, 0, 0)
    else:
        ranks = [c.rank for c in board]
        suits = [c.suit for c in board]
        paired = 1 if max(Counter(ranks).values()) >= 2 else 0
        flush_y = 1 if max(Counter(suits).values()) >= 3 else 0
        bf = (min(n, 5), paired, flush_y)

    return (hand, state.street, position, sb, ob, pb, tb, bf)


def _sim_reachable_states(
    version: str,
    episodes: int,
    seed: int,
    combined_bb_total: float,
    sb_bb: float,
    bb_bb: float,
) -> Set[Tuple[Any, ...]]:
    if episodes <= 0:
        return set()

    rng = random.Random(seed)
    bb_chips = 20
    sb_chips = int(round(sb_bb * bb_chips))
    total_chips = int(round(combined_bb_total * bb_chips))
    reachable: Set[Tuple[Any, ...]] = set()
    button = 0

    for _ in range(episodes):
        s0 = rng.randint(0, total_chips)
        s1 = total_chips - s0
        state = new_hand(
            stacks=[s0, s1],
            rng=rng,
            button=button,
            sb_chips=sb_chips,
            bb_chips=bb_chips,
        )
        button = 1 - button
        while state.phase in {"preflop", "flop", "turn", "river"}:
            hero = state.actor
            if version == "coarse":
                reachable.add(encode_from_hand_state(state, hero))
            else:
                reachable.add(_encode_legacy_from_hand_state(state, hero))
            acts = legal_actions(state)
            if not acts:
                break
            apply_action(state, rng.choice(acts))
    return reachable


def main() -> None:
    args = _parse_args()
    ckpt = args.checkpoint
    if not ckpt.exists():
        raise SystemExit(f"Checkpoint not found: {ckpt}")
    if args.reachable_sim_episodes <= 0:
        raise SystemExit("--reachable-sim-episodes must be > 0 (theoretical coverage was removed).")

    agent = RLPokerAgent.load(ckpt)
    q = agent.q
    n_states = len(q)

    version = "coarse"
    for s in q.keys():
        if isinstance(s, tuple) and s:
            if isinstance(s[0], str) and s[0].startswith("v"):
                version = "coarse"
            else:
                version = "legacy"
            break

    sim_reachable = _sim_reachable_states(
        version=version,
        episodes=args.reachable_sim_episodes,
        seed=args.reachable_sim_seed,
        combined_bb_total=args.combined_bb_total,
        sb_bb=args.sb_bb,
        bb_bb=args.bb_bb,
    )
    reachable_sim_states = len(sim_reachable)
    q_keys = set(q.keys())
    sampled_overlap = len(q_keys & sim_reachable)
    missing_in_policy = sim_reachable - q_keys

    street_counts: Counter[str] = Counter()
    hand_kind_counts: Counter[str] = Counter()
    nonzero_sa = 0
    total_sa = 0
    greedy_action_counts: Counter[str] = Counter()

    for s, row in q.items():
        street_counts[_safe_get_street(s)] += 1
        hand_kind_counts[_safe_get_hand_kind(s)] += 1

        vals = list(row.values())
        total_sa += len(vals)
        nonzero_sa += sum(1 for v in vals if abs(v) > 1e-12)

        best = max(vals) if vals else 0.0
        for a, v in row.items():
            if v == best:
                greedy_action_counts[a] += 1

    print(f"checkpoint: {ckpt}")
    print(f"episodes_completed: {agent._training_extra.get('episodes_completed', 'unknown')}")
    print(f"encoder_family: {version}")
    print("")
    print("=== Sampled reachable coverage ===")
    print(
        f"sim_reachable_states: {reachable_sim_states} "
        f"(episodes={args.reachable_sim_episodes}, seed={args.reachable_sim_seed}, "
        f"combined_bb_total={args.combined_bb_total}, sb_bb={args.sb_bb}, bb_bb={args.bb_bb})"
    )
    print(f"policy_unique_states: {n_states}")
    if reachable_sim_states > 0:
        pct = 100.0 * sampled_overlap / reachable_sim_states
        print(f"sim_reachable_overlap: {sampled_overlap}/{reachable_sim_states} ({pct:.2f}%)")
    else:
        print("sim_reachable_overlap: n/a (empty sample)")
    print(f"sim_missing_from_policy: {len(missing_in_policy)} (reachable in sample, no Q row)")
    if args.save_missing_states is not None:
        out = Path(args.save_missing_states)
        out.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 1,
            "encoder_family": version,
            "checkpoint": str(ckpt.resolve()),
            "reachable_sim_episodes": args.reachable_sim_episodes,
            "reachable_sim_seed": args.reachable_sim_seed,
            "combined_bb_total": args.combined_bb_total,
            "sb_bb": args.sb_bb,
            "bb_bb": args.bb_bb,
            "missing_states": sorted(missing_in_policy, key=repr),
        }
        with out.open("wb") as f:
            pickle.dump(payload, f, protocol=pickle.HIGHEST_PROTOCOL)
        print(f"saved missing encodings to {out} ({len(missing_in_policy)} states)")
    if total_sa > 0:
        print(f"nonzero_state_actions: {nonzero_sa}/{total_sa} ({100.0 * nonzero_sa / total_sa:.2f}%)")

    print("")
    print("=== States by Street (policy) ===")
    for street, c in street_counts.most_common(args.head):
        print(f"{street:>8}: {c:>8} ({100.0 * c / max(n_states, 1):5.2f}%)")

    print("")
    print("=== States by Hand Kind (policy) ===")
    for hk, c in hand_kind_counts.most_common(args.head):
        print(f"{hk:>8}: {c:>8} ({100.0 * c / max(n_states, 1):5.2f}%)")

    print("")
    print("=== Greedy-Action Tie Count by State ===")
    denom = max(sum(greedy_action_counts.values()), 1)
    for a, c in greedy_action_counts.most_common(args.head):
        print(f"{a:>18}: {c:>8} ({100.0 * c / denom:5.2f}%)")


if __name__ == "__main__":
    main()
