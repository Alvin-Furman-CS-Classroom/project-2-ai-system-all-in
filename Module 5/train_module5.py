#!/usr/bin/env python3
"""
Long-run self-play training with checkpoints and optional resume.

Example:

  python3 "Module 5/train_module5.py" --episodes 5000 --save-every 500 --checkpoint "Module 5/checkpoints/policy.pkl"

  python3 "Module 5/train_module5.py" --episodes 2000 --resume --checkpoint "Module 5/checkpoints/policy.pkl"
"""

from __future__ import annotations

import argparse
import datetime as dt
import random
import signal
import subprocess
import sys
from pathlib import Path

import module5_paths

module5_paths.ensure_module5_paths()

from action_mapping import DISCRETE_BUCKETS
from rl_agent import RLPokerAgent
from trainer import evaluate_bb_per_hand, train_self_play


def _git_commit_short() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(module5_paths.PROJECT_ROOT),
            text=True,
        )
        return out.strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return "unknown"


def _build_training_meta(
    args: argparse.Namespace,
    *,
    episodes_completed: int,
    final_button: int,
    randomize_stacks: bool,
    random_legal_opponent_prob: float,
) -> dict:
    return {
        "episodes_completed": int(episodes_completed),
        "final_button": int(final_button) & 1,
        "training_script": str(Path(__file__).name),
        "saved_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "git_commit": _git_commit_short(),
        "training_config": {
            "episodes_requested_this_invocation": int(args.episodes),
            "save_every": int(args.save_every),
            "resume": bool(args.resume),
            "seed": args.seed,
            "alpha": float(args.alpha),
            "gamma": float(args.gamma),
            "epsilon_schedule": int(args.epsilon_schedule),
            "epsilon_start": float(args.epsilon_start),
            "epsilon_end": float(args.epsilon_end),
            "epsilon_decay_fraction": float(args.epsilon_decay_fraction),
            "bb_chips": int(args.bb_chips),
            "sb_chips": int(args.sb_chips),
            "randomize_stacks": bool(randomize_stacks),
            "starting_bb_each": int(args.starting_bb_each),
            "combined_bb_total": int(args.combined_bb_total),
            "min_stack_bb": int(args.min_stack_bb),
            "stack_sampling_mode": str(args.stack_sampling_mode),
            "stack_sampling_extreme_prob": float(args.stack_sampling_extreme_prob),
            "count_bonus_c": float(args.count_bonus_c),
            "random_legal_opponent_prob": float(random_legal_opponent_prob),
        },
    }


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Train Module 5 RL agent (self-play on full_game_engine).")
    p.add_argument("--episodes", type=int, default=1000, help="Episodes to run this invocation")
    p.add_argument(
        "--checkpoint",
        type=Path,
        default=module5_paths.MODULE_DIR / "checkpoints" / "policy.pkl",
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
        help="Global schedule length T for epsilon decay; use same T when resuming long runs",
    )
    p.add_argument("--epsilon-start", type=float, default=0.2, help="Epsilon at start of decay window")
    p.add_argument("--epsilon-end", type=float, default=0.02, help="Epsilon after decay completes")
    p.add_argument(
        "--epsilon-decay-fraction",
        type=float,
        default=0.7,
        help="Linear decay over first (fraction * T) global episodes, then epsilon-end",
    )
    p.add_argument(
        "--stack-sampling-mode",
        choices=["uniform", "extreme_mix"],
        default="uniform",
        help="How random combined stacks are sampled when random stacks are enabled",
    )
    p.add_argument(
        "--stack-sampling-extreme-prob",
        type=float,
        default=0.6,
        help="With extreme_mix, probability of sampling from short/deep tail bands",
    )
    p.add_argument(
        "--count-bonus-c",
        type=float,
        default=0.0,
        help="Count-based exploration bonus (0 disables); adds bonus_c/sqrt(1+N(s,a)) to greedy scores",
    )
    p.add_argument("--eval-episodes", type=int, default=200)
    p.add_argument("--no-eval", action="store_true", help="Skip greedy eval at end")
    p.add_argument("--alpha", type=float, default=0.1)
    p.add_argument("--gamma", type=float, default=0.95)
    p.add_argument(
        "--random-legal-opponent-prob",
        type=float,
        default=0.0,
        metavar="P",
        help="Per-episode probability that one random seat uses random legal actions; the other uses RL (0=off)",
    )
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
    randomize = not args.no_random_stacks
    rlo = max(0.0, min(1.0, args.random_legal_opponent_prob))

    live_progress: dict[str, int] = {
        "episodes_done": episodes_completed,
        "button": int(button) & 1,
    }

    def save_now(reason: str) -> None:
        nonlocal episodes_completed, button
        agent.save(
            checkpoint,
            extra=_build_training_meta(
                args,
                episodes_completed=episodes_completed,
                final_button=button,
                randomize_stacks=randomize,
                random_legal_opponent_prob=rlo,
            ),
        )
        print(f"Saved {checkpoint} ({reason}, episodes_completed={episodes_completed}).")

    def on_sigint(_sig, _frame) -> None:
        print("\nInterrupt — saving checkpoint...", file=sys.stderr)
        agent.save(
            checkpoint,
            extra=_build_training_meta(
                args,
                episodes_completed=int(live_progress["episodes_done"]),
                final_button=int(live_progress["button"]) & 1,
                randomize_stacks=randomize,
                random_legal_opponent_prob=rlo,
            ),
        )
        print(
            f"Saved {checkpoint} (interrupt, episodes_completed={live_progress['episodes_done']}).",
            file=sys.stderr,
        )
        sys.exit(130)

    signal.signal(signal.SIGINT, on_sigint)

    stack_desc = (
        f"random split of {args.combined_bb_total} BB total"
        if randomize
        else f"equal {args.starting_bb_each} BB each"
    )
    print(
        f"Training {remaining} episodes (epsilon_schedule={args.epsilon_schedule}, "
        f"episode_index_start={episode_index_start}, stacks={stack_desc}, "
        f"random_legal_opponent_prob={rlo})..."
    )

    while remaining > 0:
        if save_every > 0:
            chunk = min(save_every, remaining)
        else:
            chunk = remaining

        live_progress["episodes_done"] = episode_index_start
        live_progress["button"] = int(button) & 1

        _, button = train_self_play(
            agent,
            episodes=chunk,
            rng=rng,
            starting_bb_each=args.starting_bb_each,
            bb_chips=args.bb_chips,
            sb_chips=args.sb_chips,
            epsilon_start=args.epsilon_start,
            epsilon_end=args.epsilon_end,
            decay_fraction=args.epsilon_decay_fraction,
            use_masked_exploration=True,
            use_monte_carlo=True,
            initial_button=button,
            episode_index_start=episode_index_start,
            epsilon_schedule_total=args.epsilon_schedule,
            randomize_stacks=randomize,
            combined_bb_total=args.combined_bb_total,
            min_stack_bb_each=args.min_stack_bb,
            stack_sampling_mode=args.stack_sampling_mode,
            stack_sampling_extreme_prob=args.stack_sampling_extreme_prob,
            count_bonus_c=args.count_bonus_c,
            live_progress=live_progress,
            random_legal_opponent_prob=rlo,
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
            stack_sampling_mode=args.stack_sampling_mode,
            stack_sampling_extreme_prob=args.stack_sampling_extreme_prob,
        )
        print(f"Greedy eval ({args.eval_episodes} hands): seat0={ev.mean_seat0:.4f}, seat1={ev.mean_seat1:.4f}, "
              f"seat0-seat1={ev.mean_seat_diff:.4f}")

    print("Done.")


if __name__ == "__main__":
    main()
