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


def map_bucket_to_action(state: HandState, bucket: str) -> Dict[str, Any]:
    if bucket not in DISCRETE_BUCKETS:
        raise ValueError(f"Unknown bucket: {bucket}")

    acts = legal_actions(state)
    if not acts:
        raise ValueError("No legal actions")

    p = state.actor
    tc = state.to_call(p)
    cur = state.round_contrib[p]
    stack = state.stacks[p]
    bb = state.bb_chips
    pot = state.pot

    def first_kind(k: str) -> Optional[Dict[str, Any]]:
        for a in acts:
            if a.get("kind") == k:
                return dict(a)
        return None

    if bucket == "fold":
        a = first_kind("fold")
        if a:
            return a
        a = first_kind("check")
        if a:
            return a
        c = first_kind("call")
        if c:
            return c
        return dict(acts[0])

    if bucket == "check_call":
        if tc == 0:
            a = first_kind("check")
            if a:
                return a
        a = first_kind("call")
        if a:
            return a
        a = first_kind("check")
        if a:
            return a
        return dict(acts[0])

    if bucket == "all_in":
        max_total = cur + stack
        totals = _raise_totals(state)
        best_t: Optional[int] = None
        for t in totals:
            if t <= max_total and (best_t is None or t > best_t):
                best_t = t
        if best_t is not None:
            return {"kind": "raise_to", "total": best_t}
        a = first_kind("call")
        if a:
            return a
        a = first_kind("check")
        if a:
            return a
        return dict(acts[0])

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
        a = first_kind("call")
        if a:
            return a
    a = first_kind("check")
    if a:
        return a
    a = first_kind("call")
    if a:
        return a
    return dict(acts[0])
