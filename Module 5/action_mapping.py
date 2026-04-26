"""
Map discrete RL action buckets to legal full_game_engine actions.

Buckets follow Module 5/README.md (pot-relative raises when raising is legal).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from full_game_engine.hu_hand import HandState, legal_actions


def legal_buckets(state: HandState) -> List[str]:
    """
    Representative discrete buckets for the current decision: one entry per *distinct*
    mapped engine action (avoids exploring duplicate buckets that map to the same fold/check/call/raise).
    """
    by_key: Dict[Tuple[Any, Any], str] = {}
    for b in DISCRETE_BUCKETS:
        act = map_bucket_to_action(state, b)
        key = (act.get("kind"), act.get("total"))
        if key not in by_key:
            by_key[key] = b
    return list(by_key.values())


DISCRETE_BUCKETS: List[str] = [
    "fold",
    "check_call",
    "bet_raise_0.5_pot",
    "bet_raise_0.75_pot",
    "bet_raise_1.0_pot",
    "bet_raise_1.5_pot",
    "all_in",
]


def _raise_totals(state: HandState) -> List[int]:
    return sorted({int(a["total"]) for a in legal_actions(state) if a.get("kind") == "raise_to"})


def _closest_raise(state: HandState, target_total: int) -> Optional[Dict[str, Any]]:
    totals = _raise_totals(state)
    if not totals:
        return None
    best = min(totals, key=lambda t: abs(t - target_total))
    return {"kind": "raise_to", "total": best}


def _first_kind(acts: List[Dict[str, Any]], k: str) -> Optional[Dict[str, Any]]:
    for a in acts:
        if a.get("kind") == k:
            return dict(a)
    return None


def _map_fold_bucket(acts: List[Dict[str, Any]]) -> Dict[str, Any]:
    a = _first_kind(acts, "fold")
    if a:
        return a
    a = _first_kind(acts, "check")
    if a:
        return a
    c = _first_kind(acts, "call")
    if c:
        return c
    return dict(acts[0])


def _map_check_call_bucket(state: HandState, acts: List[Dict[str, Any]]) -> Dict[str, Any]:
    p = state.actor
    tc = state.to_call(p)
    if tc == 0:
        a = _first_kind(acts, "check")
        if a:
            return a
    a = _first_kind(acts, "call")
    if a:
        return a
    a = _first_kind(acts, "check")
    if a:
        return a
    return dict(acts[0])


def _map_all_in_bucket(state: HandState, acts: List[Dict[str, Any]]) -> Dict[str, Any]:
    p = state.actor
    cur = state.round_contrib[p]
    stack = state.stacks[p]
    max_total = cur + stack
    totals = _raise_totals(state)
    best_t: Optional[int] = None
    for t in totals:
        if t <= max_total and (best_t is None or t > best_t):
            best_t = t
    if best_t is not None:
        return {"kind": "raise_to", "total": best_t}
    a = _first_kind(acts, "call")
    if a:
        return a
    a = _first_kind(acts, "check")
    if a:
        return a
    return dict(acts[0])


def _map_pot_fraction_raise(
    state: HandState,
    acts: List[Dict[str, Any]],
    bucket: str,
) -> Dict[str, Any]:
    p = state.actor
    tc = state.to_call(p)
    cur = state.round_contrib[p]
    stack = state.stacks[p]
    bb = state.bb_chips
    pot = state.pot

    frac = {
        "bet_raise_0.5_pot": 0.5,
        "bet_raise_0.75_pot": 0.75,
        "bet_raise_1.0_pot": 1.0,
        "bet_raise_1.5_pot": 1.5,
    }[bucket]
    base = max(pot + tc, bb)
    increment = max(bb, int(frac * base))
    target_total = min(cur + tc + increment, cur + stack)

    ra = _closest_raise(state, target_total)
    if ra is not None:
        return ra
    if tc > 0:
        a = _first_kind(acts, "call")
        if a:
            return a
    a = _first_kind(acts, "check")
    if a:
        return a
    a = _first_kind(acts, "call")
    if a:
        return a
    return dict(acts[0])


def map_bucket_to_action(state: HandState, bucket: str) -> Dict[str, Any]:
    if bucket not in DISCRETE_BUCKETS:
        raise ValueError(f"Unknown bucket: {bucket}")

    acts = legal_actions(state)
    if not acts:
        raise ValueError("No legal actions")

    if bucket == "fold":
        return _map_fold_bucket(acts)
    if bucket == "check_call":
        return _map_check_call_bucket(state, acts)
    if bucket == "all_in":
        return _map_all_in_bucket(state, acts)
    if bucket.startswith("bet_raise_"):
        return _map_pot_fraction_raise(state, acts, bucket)
    raise ValueError(f"Unhandled bucket: {bucket}")
