"""
Shared import-path bootstrap helpers for runnable scripts.

Use this module instead of repeating ``sys.path`` insertion snippets.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

PROJECT_ROOT = Path(__file__).resolve().parent


def ensure_paths(paths: Iterable[Path]) -> None:
    """Insert the given paths at the front of ``sys.path`` if absent."""
    for p in paths:
        s = str(p.resolve())
        if s not in sys.path:
            sys.path.insert(0, s)


def ensure_project_root() -> None:
    """Ensure repository root is importable."""
    ensure_paths((PROJECT_ROOT,))
