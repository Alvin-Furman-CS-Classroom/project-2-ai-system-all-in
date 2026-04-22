#!/usr/bin/env python3
"""
Round-robin benchmark for full-game agents.

Agents:
- Module 2 adapter: m2
- Module 3 adapter: m3
- Module 4 LLM: m4
- Module 5 policies: rl_optimal, rl_coverage
- Baseline: random

Reports per matchup:
- bb/100 with 95% CI
- hand win rate / tie rate
- action legality rate
- decision error rate
- fallback-to-random rate
- average decision time
"""

from __future__ import annotations

import argparse
import itertools
import math
import os
import random
import statistics
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

os.environ.setdefault("MPLBACKEND", "Agg")

import numpy as np
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from full_game_engine.bot_agents import pick_bot_action
from full_game_engine.hu_hand import apply_action, legal_actions, new_hand, random_legal_action

AGENTS = ["m2", "m3", "m4", "rl_optimal", "rl_coverage", "random"]
DISPLAY_NAMES = {
    "m2": "logic",
    "m3": "monte carlo",
    "m4": "LLM",
    "rl_optimal": "rl optimal",
    "rl_coverage": "rl coverage",
    "random": "random",
}


@dataclass
class AgentMetrics:
    hand_deltas_bb: List[float]
    hand_wins: int = 0
    hand_ties: int = 0
    decisions: int = 0
    illegal_actions: int = 0
    decision_errors: int = 0
    fallbacks_to_random: int = 0
    decision_time_ms_total: float = 0.0
    seat_sb_hands: int = 0
    seat_bb_hands: int = 0


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Benchmark full-game agent matchups.")
    p.add_argument("--hands", type=int, default=10_000, help="Hands for non-LLM matchups.")
    p.add_argument("--llm-hands", type=int, default=50, help="Hands for matchups where m4 appears.")
    p.add_argument("--seed", type=int, default=1337, help="RNG seed.")
    p.add_argument("--bb-chips", type=int, default=20)
    p.add_argument("--sb-chips", type=int, default=10)
    p.add_argument("--stack-bb", type=int, default=100, help="Starting stack for each player in BB.")
    p.add_argument(
        "--report-path",
        type=str,
        default=str(ROOT / "docs" / "AGENT_MATCHUP_REPORT.md"),
        help="Output markdown report path.",
    )
    p.add_argument(
        "--heatmap-path",
        type=str,
        default=str(ROOT / "docs" / "agent_matchup_heatmap.png"),
        help="Output image path for pairwise bb/100 heatmap.",
    )
    p.add_argument(
        "--no-heatmap",
        action="store_true",
        help="Skip generating the heatmap image.",
    )
    p.add_argument(
        "--include-self-matchups",
        action="store_true",
        help="Include self-play matchups (e.g., m2 vs m2).",
    )
    p.add_argument(
        "--self-only",
        action="store_true",
        help="Run only self-play matchups for each agent.",
    )
    return p.parse_args()


def _mean_ci95(vals: List[float]) -> Tuple[float, float, float]:
    """Return mean and 95% CI bounds for the mean."""
    if not vals:
        return 0.0, 0.0, 0.0
    mean = sum(vals) / len(vals)
    if len(vals) == 1:
        return mean, mean, mean
    std = statistics.stdev(vals)
    margin = 1.96 * std / math.sqrt(len(vals))
    return mean, mean - margin, mean + margin


def _pick_action_with_metrics(
    agent: str,
    state: Any,
    rng: random.Random,
    metrics: AgentMetrics,
) -> Dict[str, Any]:
    metrics.decisions += 1
    start = time.perf_counter()
    try:
        if agent == "random":
            act = random_legal_action(state, rng)
            meta = None
        else:
            act, meta = pick_bot_action(agent, state, rng)
    except Exception:
        metrics.decision_errors += 1
        metrics.fallbacks_to_random += 1
        act = random_legal_action(state, rng)
        meta = {"fallback": "random_legal"}
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    metrics.decision_time_ms_total += elapsed_ms

    legals = legal_actions(state)
    if act not in legals:
        metrics.illegal_actions += 1
        metrics.fallbacks_to_random += 1
        act = random_legal_action(state, rng)

    if isinstance(meta, dict) and meta.get("fallback"):
        metrics.fallbacks_to_random += 1
    return act


def _run_matchup(
    agent_a: str,
    agent_b: str,
    hands: int,
    rng: random.Random,
    bb_chips: int,
    sb_chips: int,
    stack_bb: int,
) -> Dict[str, Any]:
    m_a = AgentMetrics(hand_deltas_bb=[])
    m_b = AgentMetrics(hand_deltas_bb=[])
    button = 0

    for _ in range(hands):
        initial_stacks = [stack_bb * bb_chips, stack_bb * bb_chips]
        state = new_hand(stacks=initial_stacks, rng=rng, button=button, sb_chips=sb_chips, bb_chips=bb_chips)
        # Use pre-blind stacks as the per-hand baseline so bb/100 is zero-sum.
        start_stacks = initial_stacks
        # seat 0/1 map to agents A/B
        if button == 0:
            m_a.seat_sb_hands += 1
            m_b.seat_bb_hands += 1
        else:
            m_b.seat_sb_hands += 1
            m_a.seat_bb_hands += 1

        while state.phase in {"preflop", "flop", "turn", "river"}:
            if not legal_actions(state):
                break
            if state.actor == 0:
                action = _pick_action_with_metrics(agent_a, state, rng, m_a)
            else:
                action = _pick_action_with_metrics(agent_b, state, rng, m_b)
            apply_action(state, action)
            if state.phase == "hand_over":
                break

        d0 = (state.stacks[0] - start_stacks[0]) / float(bb_chips)
        d1 = (state.stacks[1] - start_stacks[1]) / float(bb_chips)
        m_a.hand_deltas_bb.append(d0)
        m_b.hand_deltas_bb.append(d1)
        if d0 > d1:
            m_a.hand_wins += 1
        elif d1 > d0:
            m_b.hand_wins += 1
        else:
            m_a.hand_ties += 1
            m_b.hand_ties += 1
        button = 1 - button

    def _summarize(m: AgentMetrics, total_hands: int) -> Dict[str, float]:
        mean, lo, hi = _mean_ci95(m.hand_deltas_bb)
        win_rate = m.hand_wins / float(total_hands) if total_hands else 0.0
        tie_rate = m.hand_ties / float(total_hands) if total_hands else 0.0
        legality = 1.0 - (m.illegal_actions / float(m.decisions)) if m.decisions else 1.0
        err = m.decision_errors / float(m.decisions) if m.decisions else 0.0
        fb = m.fallbacks_to_random / float(m.decisions) if m.decisions else 0.0
        avg_ms = m.decision_time_ms_total / float(m.decisions) if m.decisions else 0.0
        return {
            "bb100": mean * 100.0,
            "bb100_ci_low": lo * 100.0,
            "bb100_ci_high": hi * 100.0,
            "win_rate": win_rate,
            "tie_rate": tie_rate,
            "legality_rate": legality,
            "error_rate": err,
            "fallback_rate": fb,
            "avg_decision_ms": avg_ms,
            "hands_as_sb": float(m.seat_sb_hands),
            "hands_as_bb": float(m.seat_bb_hands),
            "decisions": float(m.decisions),
        }

    return {
        "agent_a": agent_a,
        "agent_b": agent_b,
        "hands": hands,
        "a": _summarize(m_a, hands),
        "b": _summarize(m_b, hands),
    }


def _pct(x: float) -> str:
    return f"{100.0 * x:.2f}%"


def _fmt(x: float) -> str:
    return f"{x:.3f}"


def _to_markdown(results: List[Dict[str, Any]], args: argparse.Namespace) -> str:
    lines: List[str] = []
    lines.append("# Full-Game Agent Effectiveness Report")
    lines.append("")
    lines.append("## Setup")
    lines.append(f"- Agents: `{', '.join(AGENTS)}`")
    lines.append(f"- Hands per non-LLM matchup: `{args.hands}`")
    lines.append(f"- Hands per LLM matchup (includes `m4`): `{args.llm_hands}`")
    lines.append(f"- Starting stacks: `{args.stack_bb} BB` each (`{args.stack_bb * args.bb_chips}` chips)")
    lines.append(f"- Blinds: `SB={args.sb_chips}`, `BB={args.bb_chips}`")
    lines.append(f"- Seed: `{args.seed}`")
    lines.append("")
    lines.append("## Matchup Results")
    lines.append("")

    for r in results:
        a = r["a"]
        b = r["b"]
        lines.append(f"### {r['agent_a']} vs {r['agent_b']} (`{r['hands']}` hands)")
        lines.append("")
        lines.append("| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
        lines.append(
            f"| {r['agent_a']} | {_fmt(a['bb100'])} | [{_fmt(a['bb100_ci_low'])}, {_fmt(a['bb100_ci_high'])}] | {_pct(a['win_rate'])} | {_pct(a['tie_rate'])} | {_pct(a['legality_rate'])} | {_pct(a['error_rate'])} | {_pct(a['fallback_rate'])} | {_fmt(a['avg_decision_ms'])} | {int(a['hands_as_sb'])} | {int(a['hands_as_bb'])} | {int(a['decisions'])} |"
        )
        lines.append(
            f"| {r['agent_b']} | {_fmt(b['bb100'])} | [{_fmt(b['bb100_ci_low'])}, {_fmt(b['bb100_ci_high'])}] | {_pct(b['win_rate'])} | {_pct(b['tie_rate'])} | {_pct(b['legality_rate'])} | {_pct(b['error_rate'])} | {_pct(b['fallback_rate'])} | {_fmt(b['avg_decision_ms'])} | {int(b['hands_as_sb'])} | {int(b['hands_as_bb'])} | {int(b['decisions'])} |"
        )
        lines.append("")

    return "\n".join(lines) + "\n"


def _build_bb100_matrix(results: List[Dict[str, Any]]) -> np.ndarray:
    size = len(AGENTS)
    matrix = np.full((size, size), np.nan, dtype=float)
    idx = {agent: i for i, agent in enumerate(AGENTS)}

    for result in results:
        a = result["agent_a"]
        b = result["agent_b"]
        i = idx[a]
        j = idx[b]
        a_bb100 = float(result["a"]["bb100"])
        if i == j:
            # Self-play has two rows for the same agent with opposite signs.
            # Display the positive side on the diagonal for readability.
            b_bb100 = float(result["b"]["bb100"])
            matrix[i, i] = max(a_bb100, b_bb100)
        else:
            matrix[i, j] = a_bb100
            matrix[j, i] = -a_bb100
    return matrix


def _write_heatmap(results: List[Dict[str, Any]], heatmap_path: Path) -> None:
    matrix = _build_bb100_matrix(results)
    labels = [DISPLAY_NAMES.get(agent, agent) for agent in AGENTS]

    finite_vals = matrix[np.isfinite(matrix)]
    vmax = max(1.0, float(np.nanmax(np.abs(finite_vals))))

    fig, ax = plt.subplots(figsize=(8.5, 7.0), constrained_layout=True)
    im = ax.imshow(matrix, cmap="RdYlGn", vmin=-vmax, vmax=vmax)

    ax.set_xticks(np.arange(len(labels)))
    ax.set_yticks(np.arange(len(labels)))
    ax.set_xticklabels(labels, rotation=25, ha="right")
    ax.set_yticklabels(labels)
    ax.set_title("Pairwise Agent Edge (bb/100)")

    for i in range(len(labels)):
        for j in range(len(labels)):
            val = matrix[i, j]
            text = f"{int(round(val))}" if np.isfinite(val) else "—"
            ax.text(j, i, text, ha="center", va="center", fontsize=10, color="black")

    ax.spines[:].set_visible(False)
    ax.set_xticks(np.arange(-0.5, len(labels), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(labels), 1), minor=True)
    ax.grid(which="minor", color="white", linestyle="-", linewidth=1.2)
    ax.tick_params(which="minor", bottom=False, left=False)

    cbar = fig.colorbar(im, ax=ax, shrink=0.9, pad=0.02)
    cbar.set_label("bb/100")

    heatmap_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(heatmap_path, dpi=220)
    plt.close(fig)


def main() -> None:
    args = _parse_args()
    rng = random.Random(args.seed)
    results: List[Dict[str, Any]] = []

    if args.self_only:
        pairs = [(agent, agent) for agent in AGENTS]
    elif args.include_self_matchups:
        pairs = list(itertools.combinations_with_replacement(AGENTS, 2))
    else:
        pairs = list(itertools.combinations(AGENTS, 2))
    for a, b in pairs:
        n_hands = args.llm_hands if ("m4" in (a, b)) else args.hands
        print(f"Running matchup {a} vs {b} ({n_hands} hands)...")
        res = _run_matchup(
            agent_a=a,
            agent_b=b,
            hands=n_hands,
            rng=rng,
            bb_chips=args.bb_chips,
            sb_chips=args.sb_chips,
            stack_bb=args.stack_bb,
        )
        results.append(res)

    report = _to_markdown(results, args)
    out = Path(args.report_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    print(f"Wrote report: {out}")

    if not args.no_heatmap:
        heatmap_out = Path(args.heatmap_path)
        _write_heatmap(results, heatmap_out)
        print(f"Wrote heatmap: {heatmap_out}")


if __name__ == "__main__":
    main()
