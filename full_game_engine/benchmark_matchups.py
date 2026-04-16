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
import random
import statistics
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import project_paths

project_paths.ensure_project_root()
ROOT = project_paths.PROJECT_ROOT

from full_game_engine.bot_agents import pick_bot_action
from full_game_engine.hu_hand import apply_action, legal_actions, new_hand, random_legal_action

AGENTS = ["m2", "m3", "m4", "rl_optimal", "rl_coverage", "random"]


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
    except (RuntimeError, ValueError, TypeError, KeyError):
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
        stacks = [stack_bb * bb_chips, stack_bb * bb_chips]
        state = new_hand(stacks=stacks, rng=rng, button=button, sb_chips=sb_chips, bb_chips=bb_chips)
        start_stacks = list(state.stacks)
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


def main() -> None:
    args = _parse_args()
    rng = random.Random(args.seed)
    results: List[Dict[str, Any]] = []

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


if __name__ == "__main__":
    main()
