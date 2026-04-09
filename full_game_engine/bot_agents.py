"""
Bot policy for full_game_engine: Module 5 RL and/or Module 4 LLM (index pick).

Session agent id: ``rl`` (tabular Q policy) or ``m4`` (Ollama-backed legal index).
"""

from __future__ import annotations

import os
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

_BOT_AGENTS = frozenset({"rl", "rl_optimal", "rl_coverage", "m4"})
DEFAULT_BOT_AGENT = "rl_optimal"

_RL_AGENTS: Dict[str, Optional[RLPokerAgent]] = {}
_M4_DIR = ROOT / "Module 4"


def normalize_agent(name: Optional[str]) -> str:
    a = (name or DEFAULT_BOT_AGENT).strip().lower()
    if a == "rl":
        return "rl_optimal"
    return a if a in _BOT_AGENTS else DEFAULT_BOT_AGENT


def _resolve_rl_checkpoint(agent_key: str) -> Path:
    """
    Resolve checkpoint path for RL variants.

    Env overrides:
      - RL_POLICY_PATH: applies to alias ``rl`` only.
      - RL_OPTIMAL_POLICY_PATH: path for ``rl_optimal``.
      - RL_COVERAGE_POLICY_PATH: path for ``rl_coverage``.
    """
    checkpoints = M5 / "checkpoints"
    if agent_key == "rl_coverage":
        return Path(
            os.environ.get(
                "RL_COVERAGE_POLICY_PATH",
                str(checkpoints / "coverage.pkl"),
            )
        )
    if agent_key == "rl_optimal":
        return Path(
            os.environ.get(
                "RL_OPTIMAL_POLICY_PATH",
                str(checkpoints / "optimal.pkl"),
            )
        )
    return Path(
        os.environ.get(
            "RL_POLICY_PATH",
            str(checkpoints / "optimal.pkl"),
        )
    )


def _load_rl_agent(agent_key: str) -> Optional[RLPokerAgent]:
    """Load and cache RL policy by agent id (epsilon=0)."""
    if agent_key in _RL_AGENTS:
        return _RL_AGENTS[agent_key]
    ckpt = _resolve_rl_checkpoint(agent_key)
    if not ckpt.exists():
        _RL_AGENTS[agent_key] = None
        return None
    try:
        agent = RLPokerAgent.load(ckpt)
    except Exception:
        _RL_AGENTS[agent_key] = None
        return None
    agent.epsilon = 0.0
    _RL_AGENTS[agent_key] = agent
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


def _rl_action(state: HandState, rng: random.Random, agent_key: str) -> Dict[str, Any]:
    """Map RL bucket choice to a legal engine action; fall back to random on errors."""
    agent = _load_rl_agent(agent_key)
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
    """Dispatch to RL (``rl``/``rl_optimal``/``rl_coverage``) or Module 4 LLM (``m4``).

    Returns ``(engine_action, decision_meta)``. ``decision_meta`` is set only for ``m4``.
    """
    a = normalize_agent(agent)
    try:
        if a == "m4":
            return _m4_action(state, rng)
        return _rl_action(state, rng, a), None
    except Exception:
        return random_legal_action(state, rng), None
