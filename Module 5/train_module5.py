#!/usr/bin/env python3
"""
Long-run self-play training with checkpoints and optional resume.

Example:

  python3 "Module 5/train_module5.py" --episodes 5000 --save-every 500 --checkpoint "Module 5/checkpoints/policy.pkl"

  python3 "Module 5/train_module5.py" --episodes 2000 --resume --checkpoint "Module 5/checkpoints/policy.pkl"
"""

from __future__ import annotations

import argparse
import random
import signal
import sys
from pathlib import Path

_M5 = Path(__file__).resolve().parent
_ROOT = _M5.parent
for _p in (_ROOT, _M5):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from action_mapping import DISCRETE_BUCKETS
from rl_agent import RLPokerAgent
from trainer import evaluate_bb_per_hand, train_self_play


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Train Module 5 RL agent (self-play on full_game_engine).")
    p.add_argument("--episodes", type=int, default=1000, help="Episodes to run this invocation")
    p.add_argument(
        "--checkpoint",
        type=Path,
        default=_M5 / "checkpoints" / "policy.pkl",
        help="Policy pickle path (save / resume)",
    )
    p.add_argument(
        "--save-every",
        type=int,
        default=0,
        metavar="N",
        help="Save checkpoint every N episodes within this run (0 = only save at end of run)",
    )
    p.add_argument(
        "--resume",
        action="store_true",
        help="Load checkpoint if it exists and continue (uses stored episodes_completed + button)",
    )
    p.add_argument("--seed", type=int, default=None, help="RNG seed (default: nondeterministic)")
    p.add_argument("--starting-bb-each", type=int, default=100, help="Each player's BB when using equal stacks (--no-random-stacks)")
    p.add_argument(
        "--no-random-stacks",
        action="store_true",
        help="Equal stacks for both players (--starting-bb-each each); default is random split of combined total",
    )
    p.add_argument(
        "--combined-bb-total",
        type=int,
        default=200,
        metavar="BB",
        help="Total BB in play (both stacks sum to this) when using random stacks",
    )
    p.add_argument(
        "--min-stack-bb",
        type=int,
        default=5,
        metavar="BB",
        help="Minimum stack each player when randomizing (so both can post blinds)",
    )
    p.add_argument("--bb-chips", type=int, default=20)
    p.add_argument("--sb-chips", type=int, default=10)
    p.add_argument(
        "--epsilon-schedule",
        type=int,
        default=10_000,
        metavar="T",
        help="Horizon over which epsilon decays (first 70%% of T); use a large value for long training",
    )
    p.add_argument("--eval-episodes", type=int, default=200)
    p.add_argument("--no-eval", action="store_true", help="Skip greedy eval at end")
    p.add_argument("--alpha", type=float, default=0.1)
    p.add_argument("--gamma", type=float, default=0.95)
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    rng = random.Random(args.seed) if args.seed is not None else random.Random()

    checkpoint: Path = args.checkpoint
    extra: dict = {}
    episodes_completed = 0
    button = 0

    if args.resume and checkpoint.is_file():
        agent = RLPokerAgent.load(checkpoint)
        extra = getattr(agent, "_training_extra", {}) or {}
        episodes_completed = int(extra.get("episodes_completed", 0))
        button = int(extra.get("final_button", 0)) & 1
        print(f"Resumed from {checkpoint} (episodes_completed={episodes_completed}, next_button={button}).")
    else:
        if args.resume and not checkpoint.is_file():
            print(f"No checkpoint at {checkpoint}; starting fresh.", file=sys.stderr)
        agent = RLPokerAgent(
            actions=list(DISCRETE_BUCKETS),
            alpha=args.alpha,
            gamma=args.gamma,
            epsilon=0.2,
        )

    episode_index_start = episodes_completed
    remaining = max(0, args.episodes)
    save_every = max(0, args.save_every)

    def save_now(reason: str) -> None:
        nonlocal episodes_completed, button
        agent.save(
            checkpoint,
            extra={
                "episodes_completed": episodes_completed,
                "final_button": button,
            },
        )
        print(f"Saved {checkpoint} ({reason}, episodes_completed={episodes_completed}).")

    def on_sigint(_sig, _frame) -> None:
        print("\nInterrupt — saving checkpoint...", file=sys.stderr)
        save_now("interrupt")
        sys.exit(130)

    signal.signal(signal.SIGINT, on_sigint)

    randomize = not args.no_random_stacks
    stack_desc = (
        f"random split of {args.combined_bb_total} BB total"
        if randomize
        else f"equal {args.starting_bb_each} BB each"
    )
    print(
        f"Training {remaining} episodes (epsilon_schedule={args.epsilon_schedule}, "
        f"episode_index_start={episode_index_start}, stacks={stack_desc})..."
    )

    while remaining > 0:
        if save_every > 0:
            chunk = min(save_every, remaining)
        else:
            chunk = remaining

        _, button = train_self_play(
            agent,
            episodes=chunk,
            rng=rng,
            starting_bb_each=args.starting_bb_each,
            bb_chips=args.bb_chips,
            sb_chips=args.sb_chips,
            use_masked_exploration=True,
            use_monte_carlo=True,
            initial_button=button,
            episode_index_start=episode_index_start,
            epsilon_schedule_total=args.epsilon_schedule,
            randomize_stacks=randomize,
            combined_bb_total=args.combined_bb_total,
            min_stack_bb_each=args.min_stack_bb,
        )
        episode_index_start += chunk
        episodes_completed += chunk
        remaining -= chunk

        if save_every > 0 and remaining >= 0:
            save_now(f"every {save_every} episodes")

    if save_every <= 0:
        save_now("end of run")

    if not args.no_eval:
        ev = evaluate_bb_per_hand(
            agent,
            episodes=args.eval_episodes,
            rng=random.Random((args.seed or 0) + 999),
            starting_bb_each=args.starting_bb_each,
            bb_chips=args.bb_chips,
            sb_chips=args.sb_chips,
            randomize_stacks=randomize,
            combined_bb_total=args.combined_bb_total,
            min_stack_bb_each=args.min_stack_bb,
        )
        print(f"Greedy eval ({args.eval_episodes} hands): seat0={ev.mean_seat0:.4f}, seat1={ev.mean_seat1:.4f}, "
              f"seat0-seat1={ev.mean_seat_diff:.4f}")

    print("Done.")


if __name__ == "__main__":
    main()
