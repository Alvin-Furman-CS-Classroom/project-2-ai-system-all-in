#!/usr/bin/env python3
"""
Long-run training: mostly self-play with a mixed random-legal opponent for broader
state visitation (closer to coverage_report-style reachable paths).

Default target is 100M episodes with periodic checkpoints; use --resume after interrupt.

Example:

  python3 "Module 5/train_policy_long_coverage.py"
  python3 "Module 5/train_policy_long_coverage.py" --resume --seed 42

Note: Tabular Q cannot guarantee full encoder coverage in finite time; this schedule
biases training toward visiting rare (pb, tb, line) combinations while keeping
~85% of hands as symmetric self-play.
"""

from __future__ import annotations

import argparse
import datetime as dt
import random
import signal
import subprocess
import sys
import time
from pathlib import Path

_M5 = Path(__file__).resolve().parent
_ROOT = _M5.parent
for _p in (_ROOT, _M5):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from action_mapping import DISCRETE_BUCKETS
from rl_agent import RLPokerAgent
from trainer import evaluate_bb_per_hand, train_self_play

# --- Defaults tuned for “mostly self + coverage push” over 100M episodes ---

DEFAULT_EPISODES = 100_000_000
DEFAULT_CHECKPOINT = _M5 / "checkpoints" / "policy_100m_coverage.pkl"
DEFAULT_SAVE_EVERY = 500_000
# ~85% hands: both seats RL; ~15%: one seat random legal (seat chosen uniformly).
DEFAULT_RANDOM_LEGAL_OPPONENT_PROB = 0.15
# Decay epsilon over the first half of the global schedule, then hold epsilon_end.
DEFAULT_EPSILON_SCHEDULE = DEFAULT_EPISODES
DEFAULT_EPSILON_DECAY_FRACTION = 0.5
DEFAULT_EPSILON_START = 0.2
DEFAULT_EPSILON_END = 0.02
# Wider stack buckets + short/deep tails → more (sb, ob) encoder coverage.
DEFAULT_STACK_MODE = "extreme_mix"
DEFAULT_STACK_EXTREME_PROB = 0.6


def _git_commit_short() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(_ROOT),
            text=True,
        )
        return out.strip()
    except Exception:
        return "unknown"


def _build_training_meta(
    args: argparse.Namespace,
    *,
    episodes_completed: int,
    final_button: int,
    random_legal_opponent_prob: float,
) -> dict:
    return {
        "episodes_completed": int(episodes_completed),
        "final_button": int(final_button) & 1,
        "training_script": str(Path(__file__).name),
        "saved_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "git_commit": _git_commit_short(),
        "training_config": {
            "episodes_target_total": int(args.episodes),
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
            "combined_bb_total": int(args.combined_bb_total),
            "min_stack_bb": int(args.min_stack_bb),
            "stack_sampling_mode": str(args.stack_sampling_mode),
            "stack_sampling_extreme_prob": float(args.stack_sampling_extreme_prob),
            "count_bonus_c": float(args.count_bonus_c),
            "random_legal_opponent_prob": float(random_legal_opponent_prob),
        },
    }


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Module 5: 100M-episode-style training with random-legal mix (see module docstring).",
    )
    p.add_argument("--episodes", type=int, default=DEFAULT_EPISODES, metavar="N", help="Total episodes (this run + prior if --resume)")
    p.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT, help="Policy pickle path")
    p.add_argument("--save-every", type=int, default=DEFAULT_SAVE_EVERY, metavar="N", help="Checkpoint every N episodes (required for long runs)")
    p.add_argument("--resume", action="store_true", help="Continue from checkpoint (episodes_completed + button)")
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--combined-bb-total", type=int, default=200, metavar="BB")
    p.add_argument("--min-stack-bb", type=int, default=5, metavar="BB")
    p.add_argument("--bb-chips", type=int, default=20)
    p.add_argument("--sb-chips", type=int, default=10)
    p.add_argument(
        "--random-legal-opponent-prob",
        type=float,
        default=DEFAULT_RANDOM_LEGAL_OPPONENT_PROB,
        metavar="P",
        help="Per-episode P(one seat plays random legal for the hand); rest is self-play",
    )
    p.add_argument(
        "--epsilon-schedule",
        type=int,
        default=DEFAULT_EPSILON_SCHEDULE,
        metavar="T",
        help="Global epsilon decay horizon (match --episodes for long decay)",
    )
    p.add_argument("--epsilon-start", type=float, default=DEFAULT_EPSILON_START)
    p.add_argument("--epsilon-end", type=float, default=DEFAULT_EPSILON_END)
    p.add_argument(
        "--epsilon-decay-fraction",
        type=float,
        default=DEFAULT_EPSILON_DECAY_FRACTION,
        help="Linear decay over first (fraction * epsilon-schedule) global episodes",
    )
    p.add_argument(
        "--stack-sampling-mode",
        choices=["uniform", "extreme_mix"],
        default=DEFAULT_STACK_MODE,
    )
    p.add_argument("--stack-sampling-extreme-prob", type=float, default=DEFAULT_STACK_EXTREME_PROB)
    p.add_argument(
        "--count-bonus-c",
        type=float,
        default=0.05,
        help="Count-based exploration bonus (0 disables)",
    )
    p.add_argument("--alpha", type=float, default=0.1)
    p.add_argument("--gamma", type=float, default=0.95)
    p.add_argument("--eval-episodes", type=int, default=500)
    p.add_argument("--no-eval", action="store_true", help="Skip greedy eval when the run finishes")
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    rng = random.Random(args.seed) if args.seed is not None else random.Random()

    checkpoint: Path = args.checkpoint
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
            epsilon=args.epsilon_start,
        )

    target_total = max(0, args.episodes)
    remaining = max(0, target_total - episodes_completed)
    save_every = max(1, args.save_every)
    rlo = max(0.0, min(1.0, args.random_legal_opponent_prob))
    sched = max(1, args.epsilon_schedule)

    live_progress: dict[str, int] = {
        "episodes_done": episodes_completed,
        "button": int(button) & 1,
    }

    def save_now(reason: str) -> None:
        agent.save(
            checkpoint,
            extra=_build_training_meta(
                args,
                episodes_completed=episodes_completed,
                final_button=button,
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
                random_legal_opponent_prob=rlo,
            ),
        )
        print(
            f"Saved {checkpoint} (interrupt, episodes_completed={live_progress['episodes_done']}).",
            file=sys.stderr,
        )
        sys.exit(130)

    signal.signal(signal.SIGINT, on_sigint)

    print(
        f"Long coverage training: up to {target_total} total episodes "
        f"({remaining} remaining), save_every={save_every}, "
        f"random_legal_opponent_prob={rlo}, stack_mode={args.stack_sampling_mode}, "
        f"epsilon_schedule={sched}, |Q|={len(agent.q)}"
    )
    t0 = time.perf_counter()

    episode_index_start = episodes_completed
    while remaining > 0:
        chunk = min(save_every, remaining)
        live_progress["episodes_done"] = episode_index_start
        live_progress["button"] = int(button) & 1

        _, button = train_self_play(
            agent,
            episodes=chunk,
            rng=rng,
            starting_bb_each=100,
            bb_chips=args.bb_chips,
            sb_chips=args.sb_chips,
            epsilon_start=args.epsilon_start,
            epsilon_end=args.epsilon_end,
            decay_fraction=args.epsilon_decay_fraction,
            use_masked_exploration=True,
            use_monte_carlo=True,
            initial_button=button,
            episode_index_start=episode_index_start,
            epsilon_schedule_total=sched,
            randomize_stacks=True,
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

        elapsed = time.perf_counter() - t0
        eps_per_s = episodes_completed / elapsed if elapsed > 0 else 0.0
        print(
            f"progress: episodes_completed={episodes_completed} "
            f"|Q|={len(agent.q)} "
            f"({eps_per_s:.1f} ep/s elapsed {elapsed/3600:.2f}h)"
        )
        save_now(f"every {save_every} episodes")

    if not args.no_eval:
        ev = evaluate_bb_per_hand(
            agent,
            episodes=args.eval_episodes,
            rng=random.Random((args.seed or 0) + 999),
            starting_bb_each=100,
            bb_chips=args.bb_chips,
            sb_chips=args.sb_chips,
            randomize_stacks=True,
            combined_bb_total=args.combined_bb_total,
            min_stack_bb_each=args.min_stack_bb,
            stack_sampling_mode=args.stack_sampling_mode,
            stack_sampling_extreme_prob=args.stack_sampling_extreme_prob,
        )
        print(
            f"Greedy eval ({args.eval_episodes} hands): seat0={ev.mean_seat0:.4f}, seat1={ev.mean_seat1:.4f}, "
            f"seat0-seat1={ev.mean_seat_diff:.4f}"
        )

    print("Done.")


if __name__ == "__main__":
    main()
