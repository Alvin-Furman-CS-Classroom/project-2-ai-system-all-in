"""
Single import path setup for Module 5 scripts and in-repo modules.

Runnable CLIs live under ``Module 5/``; they need the project root and this directory
on ``sys.path`` so ``full_game_engine`` and local imports resolve. Import this module
first (it lives next to the scripts, so it resolves without any prior path hack).

Usage::

    import module5_paths
    module5_paths.ensure_module5_paths()
"""

from __future__ import annotations

import sys
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = MODULE_DIR.parent


def ensure_module5_paths() -> None:
    """Insert project root and ``Module 5`` at the front of ``sys.path`` if missing."""
    for p in (PROJECT_ROOT, MODULE_DIR):
        s = str(p)
        if s not in sys.path:
            sys.path.insert(0, s)
