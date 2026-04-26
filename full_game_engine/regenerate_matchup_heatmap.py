#!/usr/bin/env python3
"""
Regenerate the pairwise bb/100 heatmap PNG from an existing
``AGENT_MATCHUP_REPORT*.md`` produced by ``benchmark_matchups.py``,
without re-running simulations.

Example:
  python -m full_game_engine.regenerate_matchup_heatmap \\
    --report-path docs/AGENT_MATCHUP_REPORT_10000_10_RERUN.md \\
    --heatmap-path docs/agent_matchup_heatmap_10000_10_rerun.png
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from full_game_engine.benchmark_matchups import _write_heatmap


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Regenerate matchup heatmap from markdown report.")
    p.add_argument(
        "--report-path",
        type=Path,
        required=True,
        help="Path to Full-Game Agent Effectiveness Report markdown.",
    )
    p.add_argument(
        "--heatmap-path",
        type=Path,
        required=True,
        help="Output PNG path for the heatmap.",
    )
    return p.parse_args()


def parse_benchmark_report_markdown(text: str) -> List[Dict[str, Any]]:
    """
    Parse ``### agent_a vs agent_b (`N` hands)`` blocks and the two result table rows.
    Returns minimal result dicts compatible with ``_write_heatmap``.
    """
    lines = text.splitlines()
    matchup_re = re.compile(r"^###\s+(\S+)\s+vs\s+(\S+)\s+\(`(\d+)` hands\)")
    row_re = re.compile(r"^\|\s*(\S+)\s*\|\s*([+-]?\d+(?:\.\d+)?)\s*\|")

    results: List[Dict[str, Any]] = []
    i = 0
    while i < len(lines):
        m = matchup_re.match(lines[i].strip())
        if not m:
            i += 1
            continue
        agent_a, agent_b = m.group(1), m.group(2)
        hands = int(m.group(3))
        i += 1
        while i < len(lines) and not lines[i].strip().startswith("| Agent |"):
            i += 1
        if i >= len(lines):
            break
        i += 1
        if i >= len(lines) or not lines[i].strip().startswith("|---"):
            continue
        i += 1
        rows: List[Tuple[str, float]] = []
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith("###") or (line.startswith("##") and not line.startswith("###")):
                break
            rm = row_re.match(line)
            if rm:
                rows.append((rm.group(1), float(rm.group(2))))
            i += 1
        if len(rows) < 2:
            continue
        # Self-play: both rows name the same agent; a dict keyed by name would
        # overwrite one seat. Use row order (matches benchmark markdown: agent_a
        # row first, agent_b row second — same id, different seats).
        if agent_a == agent_b:
            a_bb = rows[0][1]
            b_bb = rows[1][1]
        else:
            bb = {rows[0][0]: rows[0][1], rows[1][0]: rows[1][1]}
            if agent_a not in bb or agent_b not in bb:
                continue
            a_bb = bb[agent_a]
            b_bb = bb[agent_b]
        results.append(
            {
                "agent_a": agent_a,
                "agent_b": agent_b,
                "hands": hands,
                "a": {"bb100": a_bb},
                "b": {"bb100": b_bb},
            }
        )
    return results


def main() -> None:
    args = _parse_args()
    text = args.report_path.read_text(encoding="utf-8")
    results = parse_benchmark_report_markdown(text)
    if not results:
        raise SystemExit(f"No matchup blocks parsed from {args.report_path}")
    _write_heatmap(results, args.heatmap_path)
    print(f"Wrote heatmap: {args.heatmap_path} ({len(results)} matchups)")


if __name__ == "__main__":
    main()
