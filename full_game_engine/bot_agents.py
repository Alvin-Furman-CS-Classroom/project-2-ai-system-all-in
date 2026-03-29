"""
Bot policy wrapper for full_game_engine: RL agent from Module 5 only.

This replaces the earlier multi-bot routing with a single bot type "rl" that
loads `Module 5/checkpoints/my_policy.pkl` and uses the discrete action buckets
from Module 5 to select legal actions on every betting street.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from full_game_engine.hu_hand import HandState, legal_actions, random_legal_action

ROOT = Path(__file__).resolve().parent.parent

M5 = ROOT / "Module 5"
if str(M5) not in sys.path:
    sys.path.insert(0, str(M5))

from action_mapping import DISCRETE_BUCKETS, legal_buckets, map_bucket_to_action  # type: ignore  # noqa: E402
from rl_agent import RLPokerAgent  # type: ignore  # noqa: E402
from state_encoder import encode_from_hand_state  # type: ignore  # noqa: E402

_BOT_AGENTS = frozenset({"rl"})
DEFAULT_BOT_AGENT = "rl"

_RL_AGENT: Optional[RLPokerAgent] = None


def normalize_agent(name: Optional[str]) -> str:
    a = (name or DEFAULT_BOT_AGENT).strip().lower()
    return a if a in _BOT_AGENTS else DEFAULT_BOT_AGENT


def _load_rl_agent() -> Optional[RLPokerAgent]:
    """Load the RL policy from Module 5/checkpoints/my_policy.pkl (epsilon=0 for play)."""
    global _RL_AGENT
    if _RL_AGENT is not None:
        return _RL_AGENT
    ckpt = M5 / "checkpoints" / "my_policy.pkl"
    if not ckpt.exists():
        return None
    try:
        agent = RLPokerAgent.load(ckpt)
    except Exception:
        return None
    agent.epsilon = 0.0
    _RL_AGENT = agent
    return _RL_AGENT


def _rl_action(state: HandState, rng: random.Random) -> Dict[str, Any]:
    """Map RL bucket choice to a legal engine action; fall back to random on errors."""
    agent = _load_rl_agent()
    if agent is None:
        return random_legal_action(state, rng)
    if not legal_actions(state):
        raise ValueError("No legal actions")
    enc = encode_from_hand_state(state, state.actor)
    lbs = legal_buckets(state)
    if not lbs:
        return random_legal_action(state, rng)
    # If state was never visited, Q-row is created on the fly with zeros.
    bucket = agent.select_action_masked(enc, lbs)
    try:
        return map_bucket_to_action(state, bucket)
    except Exception:
        return random_legal_action(state, rng)


def pick_bot_action(agent: Optional[str], state: HandState, rng: random.Random) -> Dict[str, Any]:
    """Dispatch to RL bot only (name is kept for API compatibility)."""
    _ = normalize_agent(agent)
    try:
        return _rl_action(state, rng)
    except Exception:
        return random_legal_action(state, rng)

