#!/usr/bin/env python3
"""
Create a clean pairwise bb/100 heatmap from AGENT_MATCHUP_REPORT.md.

Expected report section:
## Pairwise Matrix (Primary View)
| Row \ Col | m2 | m3 | ... |
|---|---:|---:|...|
| m2 | — | -12.230 [10000] | ... |
...
"""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path
from typing import List, Tuple

import numpy as np

os.environ.setdefault("MPLBACKEND", "Agg")
import matplotlib.pyplot as plt


DISPLAY_NAMES = {
    "m2": "logic",
    "m3": "monte carlo",
    "m4": "LLM",
    "rl_optimal": "rl optimal",
    "rl_coverage": "rl coverage",
    "random": "random",
}


def _parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parent.parent
    p = argparse.ArgumentParser(description="Plot pairwise bb/100 heatmap from markdown report.")
    p.add_argument(
        "--report-path",
        type=Path,
        default=root / "docs" / "AGENT_MATCHUP_REPORT.md",
        help="Path to markdown report.",
    )
    p.add_argument(
        "--output-path",
        type=Path,
        default=root / "docs" / "agent_matchup_heatmap.png",
        help="Path to output PNG heatmap.",
    )
    p.add_argument(
        "--min-hands",
        type=int,
        default=0,
        help="If > 0, blank cells with hands below this threshold.",
    )
    return p.parse_args()


def _split_markdown_row(line: str) -> List[str]:
    parts = [cell.strip() for cell in line.strip().strip("|").split("|")]
    return parts


def _extract_matrix(report_text: str) -> Tuple[List[str], np.ndarray, np.ndarray]:
    lines = report_text.splitlines()
    start_idx = -1
    for i, line in enumerate(lines):
        if line.strip().startswith("| Row \\ Col |"):
            start_idx = i
            break
    if start_idx < 0:
        raise ValueError("Could not find pairwise matrix header row in report.")

    header = _split_markdown_row(lines[start_idx])
    agents = header[1:]
    size = len(agents)
    matrix = np.full((size, size), np.nan, dtype=float)
    hands = np.zeros((size, size), dtype=int)

    value_re = re.compile(r"([+\-]?\d+(?:\.\d+)?)\s*\[(\d+)\]")
    agent_to_idx = {a: i for i, a in enumerate(agents)}

    row_idx = start_idx + 2  # skip separator row
    while row_idx < len(lines):
        line = lines[row_idx].strip()
        if not line.startswith("|"):
            break
        cols = _split_markdown_row(line)
        if len(cols) != size + 1:
            break
        row_agent = cols[0]
        if row_agent not in agent_to_idx:
            break
        i = agent_to_idx[row_agent]
        for j, cell in enumerate(cols[1:]):
            if cell in {"—", "-", ""}:
                if i == j:
                    matrix[i, j] = 0.0
                continue
            m = value_re.search(cell)
            if not m:
                raise ValueError(f"Could not parse cell value: '{cell}'")
            matrix[i, j] = float(m.group(1))
            hands[i, j] = int(m.group(2))
        row_idx += 1

    return agents, matrix, hands


def _plot_heatmap(
    agents: List[str],
    matrix: np.ndarray,
    hands: np.ndarray,
    output_path: Path,
    min_hands: int,
) -> None:
    display_labels = [DISPLAY_NAMES.get(a, a.replace("_", " ")) for a in agents]

    plot_matrix = matrix.copy()
    if min_hands > 0:
        low_conf_mask = (hands < min_hands) & (~np.eye(len(agents), dtype=bool))
        plot_matrix[low_conf_mask] = np.nan

    finite_vals = plot_matrix[np.isfinite(plot_matrix)]
    vmax = max(1.0, float(np.max(np.abs(finite_vals)))) if finite_vals.size else 1.0

    fig, ax = plt.subplots(figsize=(8.5, 7.0), constrained_layout=True)
    cmap = plt.get_cmap("RdYlGn").copy()
    cmap.set_bad(color="#eeeeee")
    im = ax.imshow(plot_matrix, cmap=cmap, vmin=-vmax, vmax=vmax)

    ax.set_xticks(np.arange(len(display_labels)))
    ax.set_yticks(np.arange(len(display_labels)))
    ax.set_xticklabels(display_labels, rotation=25, ha="right")
    ax.set_yticklabels(display_labels)
    for label in ax.get_yticklabels():
        label.set_fontweight("bold")
    ax.set_title("Pairwise Agent Edge (bb/100)")

    for i in range(len(display_labels)):
        for j in range(len(display_labels)):
            if i == j:
                text = "—"
            elif not np.isfinite(plot_matrix[i, j]):
                text = ""
            else:
                text = str(int(round(plot_matrix[i, j])))
            ax.text(j, i, text, ha="center", va="center", fontsize=10, color="black")

    ax.spines[:].set_visible(False)
    ax.set_xticks(np.arange(-0.5, len(display_labels), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(display_labels), 1), minor=True)
    ax.grid(which="minor", color="white", linestyle="-", linewidth=1.2)
    ax.tick_params(which="minor", bottom=False, left=False)

    cbar = fig.colorbar(im, ax=ax, shrink=0.9, pad=0.02)
    cbar.set_label("bb/100")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=220)
    plt.close(fig)


def main() -> None:
    args = _parse_args()
    text = args.report_path.read_text(encoding="utf-8")
    agents, matrix, hands = _extract_matrix(text)
    _plot_heatmap(agents, matrix, hands, args.output_path, args.min_hands)
    print(f"Wrote heatmap: {args.output_path}")


if __name__ == "__main__":
    main()
