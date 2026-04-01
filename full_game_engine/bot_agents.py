"""
Bot policy for full_game_engine: Module 5 RL and/or Module 4 LLM (index pick).

Session agent id: ``rl`` (tabular Q policy) or ``m4`` (Ollama-backed legal index).
"""

from __future__ import annotations

import random
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from full_game_engine.hu_hand import HandState, legal_actions, random_legal_action
from full_game_engine.mc_bot import hole_cards_to_mc_hand

ROOT = Path(__file__).resolve().parent.parent

M5 = ROOT / "Module 5"
if str(M5) not in sys.path:
    sys.path.insert(0, str(M5))

from action_mapping import legal_buckets, map_bucket_to_action  # type: ignore  # noqa: E402
from rl_agent import RLPokerAgent  # type: ignore  # noqa: E402
from state_encoder import encode_from_hand_state  # type: ignore  # noqa: E402

_BOT_AGENTS = frozenset({"rl", "m4"})
DEFAULT_BOT_AGENT = "rl"

_RL_AGENT: Optional[RLPokerAgent] = None
_M4_DIR = ROOT / "Module 4"


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
    return agent


def _load_module4_choose_with_meta():
    """Import Module 4 ``choose_preflop_action_with_meta`` (folder has a space)."""
    if not _M4_DIR.is_dir():
        return None
    if str(_M4_DIR) not in sys.path:
        sys.path.insert(0, str(_M4_DIR))
    try:
        import llm_policy  # type: ignore

        return getattr(llm_policy, "choose_preflop_action_with_meta", None)
    except ImportError:
        return None


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
    bucket = agent.select_action_masked(enc, lbs)
    try:
        return map_bucket_to_action(state, bucket)
    except Exception:
        return random_legal_action(state, rng)


def _m4_action(
    state: HandState, rng: random.Random
) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
    """Module 4 LLM: index into legal_actions; fallback on error."""
    p = state.actor
    acts = legal_actions(state)
    if not acts:
        raise ValueError("No legal actions")
    c0, c1 = state.hole_cards[p]
    hand = hole_cards_to_mc_hand(c0, c1)
    choose = _load_module4_choose_with_meta()
    if choose is None:
        return random_legal_action(state, rng), None
    try:
        act, meta = choose(state, hand, acts, rng)
        enriched = dict(meta)
        enriched["street"] = str(state.street)
        return act, enriched
    except Exception as e:
        return random_legal_action(state, rng), {"fallback": "random_legal", "error": str(e)}


def pick_bot_action(
    agent: Optional[str], state: HandState, rng: random.Random
) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
    """Dispatch to RL (``rl``) or Module 4 LLM (``m4``).

    Returns ``(engine_action, decision_meta)``. ``decision_meta`` is set only for ``m4``.
    """
    a = normalize_agent(agent)
    try:
        if a == "m4":
            return _m4_action(state, rng)
        return _rl_action(state, rng), None
    except Exception:
        return random_legal_action(state, rng), None
