"""
Unified bot policies for the web UI: random baseline, Module 1+2 (A* + logic),
Module 3 (MC), Module 4 (LLM index pick, Ollama-first).
"""

from __future__ import annotations

import importlib.util
import random
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from game_engine.hu_preflop import HandState, legal_actions, random_legal_action
from game_engine.mc_bot import hole_cards_to_mc_hand, mc_or_random_action

ROOT = Path(__file__).resolve().parent.parent

_BOT_AGENTS = frozenset({"random", "m12", "m3", "m4"})
DEFAULT_BOT_AGENT = "m3"


def normalize_agent(name: Optional[str]) -> str:
    a = (name or DEFAULT_BOT_AGENT).strip().lower()
    return a if a in _BOT_AGENTS else DEFAULT_BOT_AGENT


def _load_module1_decider():
    path = ROOT / "Module 1" / "propositional_logic.py"
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location("propositional_logic_m1", path)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, "propositional_logic_hand_decider", None)


def _load_a_star():
    m2 = ROOT / "Module 2"
    if str(m2) not in sys.path:
        sys.path.insert(0, str(m2))
    try:
        from bet_sizing_search import a_star_search  # type: ignore
    except ImportError:
        return None
    return a_star_search


_m1_decider = None
_a_star_search = None
_m4_dir = ROOT / "Module 4"


def _load_module4_choose_with_meta():
    """Import Module 4 ``choose_preflop_action_with_meta`` (folder name has a space)."""
    if not _m4_dir.is_dir():
        return None
    if str(_m4_dir) not in sys.path:
        sys.path.insert(0, str(_m4_dir))
    try:
        import llm_policy  # type: ignore

        return getattr(llm_policy, "choose_preflop_action_with_meta", None)
    except ImportError:
        return None


def _m4_action(
    state: HandState, rng: random.Random
) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
    """Module 4: LLM picks an index into legal_actions; fallback on any failure."""
    p = state.actor
    legal = legal_actions(state)
    if not legal:
        raise ValueError("No legal actions")
    c0, c1 = state.hole_cards[p]
    hand = hole_cards_to_mc_hand(c0, c1)
    choose = _load_module4_choose_with_meta()
    if choose is None:
        return random_legal_action(state, rng), None
    try:
        act, meta = choose(state, hand, legal, rng)
        enriched = dict(meta)
        enriched["street"] = "preflop"
        return act, enriched
    except Exception as e:
        return random_legal_action(state, rng), {"fallback": "random_legal", "error": str(e)}


def _m12_action(state: HandState, rng: random.Random) -> Dict[str, Any]:
    """Module 1 playability + Module 2 A* bet sizing, mapped to engine legal actions."""
    global _m1_decider, _a_star_search
    p = state.actor
    legal = legal_actions(state)
    if not legal:
        raise ValueError("No legal actions")

    if _a_star_search is None:
        _a_star_search = _load_a_star()
    if _m1_decider is None:
        _m1_decider = _load_module1_decider()

    bb = float(state.bb_chips)
    human = 1 - p
    c0, c1 = state.hole_cards[p]
    hand = hole_cards_to_mc_hand(c0, c1)
    stacks_bb = (
        (state.stacks[1] / bb, state.stacks[0] / bb) if p == 1 else (state.stacks[0] / bb, state.stacks[1] / bb)
    )
    pos = "Button" if state.button == p else "Big Blind"
    to_call = state.to_call(p)
    pot_bb = max(state.pot / bb, 0.5)
    opp_bet_bb: Optional[float] = (state.round_contrib[human] / bb) if to_call > 0 else None

    if _m1_decider is not None:
        try:
            dec = _m1_decider(
                hand,
                pos,
                max(1, int(state.stacks[p] // bb)),
                "Unknown",
                opp_bet_bb,
            )
            if not dec.get("playable"):
                folds = [a for a in legal if a["kind"] == "fold"]
                if folds:
                    return folds[0]
        except Exception:
            pass

    if _a_star_search is None:
        return random_legal_action(state, rng)

    try:
        res = _a_star_search(
            hand,
            pos,
            stacks_bb,
            "Unknown",
            opp_bet_bb,
            pot_size=pot_bb,
        )
    except Exception:
        return random_legal_action(state, rng)

    action = (res.get("action") or "fold").lower()
    bet_bb = float(res.get("bet_size") or 0.0)

    if action == "fold":
        folds = [a for a in legal if a["kind"] == "fold"]
        if folds:
            return folds[0]
    if action == "call":
        calls = [a for a in legal if a["kind"] == "call"]
        if calls:
            return calls[0]
    if action == "check":
        checks = [a for a in legal if a["kind"] == "check"]
        if checks:
            return checks[0]

    target_total = int(round(bet_bb * bb))
    raises = [a for a in legal if a["kind"] == "raise_to"]
    if raises:
        return min(raises, key=lambda a: abs(a["total"] - target_total))

    return random_legal_action(state, rng)


def pick_bot_action(
    agent: Optional[str], state: HandState, rng: random.Random
) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
    """Dispatch to random / Module 1+2 / Module 3 Monte Carlo / Module 4 LLM.

    Returns ``(engine_action, decision_meta)``. ``decision_meta`` is set only for
    Module 4 (LLM reason/model, or fallback error info).
    """
    a = normalize_agent(agent)
    if a == "random":
        return random_legal_action(state, rng), None
    if a == "m12":
        try:
            return _m12_action(state, rng), None
        except Exception:
            return random_legal_action(state, rng), None
    if a == "m4":
        try:
            return _m4_action(state, rng)
        except Exception as e:
            return random_legal_action(state, rng), {"fallback": "random_legal", "error": str(e)}
    return mc_or_random_action(state, rng, use_mc=True), None
