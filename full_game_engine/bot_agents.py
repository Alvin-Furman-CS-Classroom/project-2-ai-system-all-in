"""
Bot policy for full_game_engine: Module 5 RL, Module 2 search, and Module 4 LLM.
"""

from __future__ import annotations

import os
import random
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from engine_adapter_utils import first_legal_kind, map_search_recommendation_to_action
from full_game_engine.hu_hand import HandState, legal_actions, random_legal_action
from full_game_engine.mc_bot import hole_cards_to_mc_hand, mc_or_random_action
import project_paths

ROOT = Path(__file__).resolve().parent.parent

M5 = ROOT / "Module 5"
project_paths.ensure_paths((M5,))

from action_mapping import legal_buckets, map_bucket_to_action  # type: ignore  # noqa: E402
from rl_agent import RLPokerAgent  # type: ignore  # noqa: E402
from state_encoder import encode_from_hand_state  # type: ignore  # noqa: E402

_M2_DIR = ROOT / "Module 2"
project_paths.ensure_paths((_M2_DIR,))
try:
    from bet_sizing_search import optimal_bet_sizing_search  # type: ignore  # noqa: E402
except ImportError:  # pragma: no cover
    optimal_bet_sizing_search = None  # type: ignore

_BOT_AGENTS = frozenset({"rl", "rl_optimal", "rl_coverage", "m2", "m3", "m4"})
DEFAULT_BOT_AGENT = "rl_optimal"

_RL_AGENTS: Dict[str, Optional[RLPokerAgent]] = {}
_M4_DIR = ROOT / "Module 4"


def normalize_agent(name: Optional[str]) -> str:
    a = (name or DEFAULT_BOT_AGENT).strip().lower()
    if a == "rl":
        return "rl_optimal"
    return a if a in _BOT_AGENTS else DEFAULT_BOT_AGENT


def _position_label(state: HandState, seat: int) -> str:
    return "Button" if state.button == seat else "Big Blind"


def _board_features(state: HandState, seat: int) -> Dict[str, Any]:
    board = tuple(state.board)
    suits = [c.suit for c in board]
    ranks = [c.rank for c in board]
    suit_counts: Dict[Any, int] = {}
    for s in suits:
        suit_counts[s] = suit_counts.get(s, 0) + 1
    rank_counts: Dict[Any, int] = {}
    for r in ranks:
        rank_counts[r] = rank_counts.get(r, 0) + 1

    c0, c1 = state.hole_cards[seat]
    hero_suited = c0.suit == c1.suit
    flush_draw = max(suit_counts.values(), default=0) >= 3
    wet = flush_draw or (len(ranks) >= 3 and (max(ranks) - min(ranks) <= 5))
    return {
        "board_len": len(board),
        "paired": any(v >= 2 for v in rank_counts.values()),
        "flush_draw": flush_draw,
        "wet": wet,
        "hero_suited": hero_suited,
    }


def _m2_action(state: HandState, rng: random.Random) -> Dict[str, Any]:
    """Module 2 fast heuristic full-hand adapter."""
    if optimal_bet_sizing_search is None:
        return random_legal_action(state, rng)
    acts = legal_actions(state)
    if not acts:
        raise ValueError("No legal actions")
    seat = state.actor
    c0, c1 = state.hole_cards[seat]
    hand = hole_cards_to_mc_hand(c0, c1)
    bb = float(state.bb_chips)
    context = {
        "hand": hand,
        "position": _position_label(state, seat),
        "stack_sizes": (
            int(round(state.stacks[seat] / bb)),
            int(round(state.stacks[1 - seat] / bb)),
        ),
        "opponent_tendency": "Unknown",
        "street": state.street,
        "pot_size": max(state.pot / bb, 0.5),
        "opponent_bet_size": (state.to_call(seat) / bb) if state.to_call(seat) > 0 else None,
        "board_features": _board_features(state, seat),
    }
    try:
        # Use Module 1 playability filtering preflop; skip it on later streets.
        use_module1_filter = state.street == "preflop"
        rec = optimal_bet_sizing_search(
            hand=hand,
            position=context["position"],
            stack_sizes=context["stack_sizes"],
            opponent_tendency="Unknown",
            search_algorithm="a_star",
            use_module1=use_module1_filter,
            opponent_bet_size=context["opponent_bet_size"],
            pot_size=context["pot_size"],
            full_hand_context=context,
        )
    except (RuntimeError, ValueError, TypeError, KeyError):
        return random_legal_action(state, rng)

    mapped = map_search_recommendation_to_action(
        acts,
        action_name=str(rec.get("action", "fold")),
        bet_size_bb=float(rec.get("bet_size", 0.0)),
        bb_chips=float(state.bb_chips),
    )
    if mapped is not None:
        return mapped
    call_or_check = first_legal_kind(acts, "call", "check")
    if call_or_check is not None:
        return call_or_check
    return dict(acts[0])


def _m3_action(state: HandState, rng: random.Random) -> Dict[str, Any]:
    """Module 3 Monte Carlo adapter (all-streets approximation)."""
    return mc_or_random_action(state, rng, use_mc=True)


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
    except (ValueError, OSError):
        _RL_AGENTS[agent_key] = None
        return None
    agent.epsilon = 0.0
    _RL_AGENTS[agent_key] = agent
    return agent


def _load_module4_choose_with_meta():
    """Import Module 4 ``choose_preflop_action_with_meta`` (folder has a space)."""
    if not _M4_DIR.is_dir():
        return None
    project_paths.ensure_paths((_M4_DIR,))
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
    except (ValueError, KeyError):
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
    except (RuntimeError, ValueError, TypeError, KeyError) as e:
        return random_legal_action(state, rng), {"fallback": "random_legal", "error": str(e)}


def pick_bot_action(
    agent: Optional[str], state: HandState, rng: random.Random
) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
    """Dispatch to RL, Module 2 search, Module 3 MC, or Module 4 LLM.

    Returns ``(engine_action, decision_meta)``. ``decision_meta`` is set only for ``m4``.
    """
    a = normalize_agent(agent)
    try:
        if a == "m4":
            return _m4_action(state, rng)
        if a == "m3":
            return _m3_action(state, rng), None
        if a == "m2":
            return _m2_action(state, rng), None
        return _rl_action(state, rng, a), None
    except (RuntimeError, ValueError, TypeError, KeyError):
        return random_legal_action(state, rng), None
