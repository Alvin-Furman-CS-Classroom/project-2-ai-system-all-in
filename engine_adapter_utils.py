"""
Shared helpers for mapping high-level recommendations to legal engine actions.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional


def first_legal_kind(legal_actions: Iterable[Dict[str, Any]], *kinds: str) -> Optional[Dict[str, Any]]:
    """Return the first legal action whose ``kind`` matches any requested kind."""
    wanted = set(kinds)
    for action in legal_actions:
        if action.get("kind") in wanted:
            return dict(action)
    return None


def closest_raise_to_total(
    legal_actions: Iterable[Dict[str, Any]], target_total: int
) -> Optional[Dict[str, Any]]:
    """Return raise action with ``total`` closest to ``target_total``."""
    raises = [a for a in legal_actions if a.get("kind") == "raise_to"]
    if not raises:
        return None
    return dict(min(raises, key=lambda a: abs(int(a["total"]) - int(target_total))))


def map_search_recommendation_to_action(
    legal_actions: Iterable[Dict[str, Any]],
    *,
    action_name: str,
    bet_size_bb: float,
    bb_chips: float,
) -> Optional[Dict[str, Any]]:
    """
    Convert a search recommendation (action + bet size in BB) to a legal engine action.
    """
    legal = [dict(a) for a in legal_actions]
    action = action_name.lower()
    if action == "fold":
        return first_legal_kind(legal, "fold")
    if action == "call":
        return first_legal_kind(legal, "call")
    if action == "check":
        return first_legal_kind(legal, "check")
    target_total = int(round(float(bet_size_bb) * float(bb_chips)))
    return closest_raise_to_total(legal, target_total)
