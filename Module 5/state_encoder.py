"""
State encoder for Module 5 RL agent.

Converts full_game_engine.HandState (from the current actor's perspective) into a
compact hashable tuple for tabular Q-learning.
"""

from __future__ import annotations

from collections import Counter
from typing import Tuple

from full_game_engine.cards import Card
from full_game_engine.hu_hand import HandState


def _bucket_linear(x: float, edges: Tuple[float, ...]) -> int:
    for i, e in enumerate(edges):
        if x < e:
            return i
    return len(edges)


def _encode_hole_pair(c0: Card, c1: Card) -> Tuple:
    r0, r1 = c0.rank, c1.rank
    if r0 == r1:
        return ("pair", _bucket_linear(float(r0), (5.0, 9.0, 11.0)))
    hi, lo = max(r0, r1), min(r0, r1)
    suited = 1 if c0.suit == c1.suit else 0
    return ("np", _bucket_linear(float(hi), (6.0, 9.0, 11.0)), _bucket_linear(float(lo), (4.0, 8.0)), suited)


def _board_feats(board: Tuple[Card, ...]) -> Tuple[int, int, int]:
    n = len(board)
    if n == 0:
        return (0, 0, 0)
    ranks = [c.rank for c in board]
    suits = [c.suit for c in board]
    rc = Counter(ranks)
    paired = 1 if max(rc.values()) >= 2 else 0
    sc = Counter(suits)
    flush_y = 1 if max(sc.values()) >= 3 else 0
    return (min(n, 5), paired, flush_y)


def encode_from_hand_state(state: HandState, hero: int) -> Tuple:
    """
    Encode state from hero's perspective (hero is usually state.actor during training).

    Uses coarse buckets to keep the Q-table tractable.
    """
    bb = float(state.bb_chips)
    hole = state.hole_cards[hero]
    hand = _encode_hole_pair(hole[0], hole[1])

    street = state.street
    position = 1 if hero == state.button else 0  # 1 = BTN, 0 = BB

    my_stack_bb = state.stacks[hero] / bb
    opp_stack_bb = state.stacks[1 - hero] / bb
    pot_bb = state.pot / bb
    tc_bb = state.to_call(hero) / bb

    sb = _bucket_linear(my_stack_bb, (15.0, 40.0, 100.0))
    ob = _bucket_linear(opp_stack_bb, (15.0, 40.0, 100.0))
    pb = _bucket_linear(pot_bb, (2.0, 8.0, 20.0))
    tb = _bucket_linear(tc_bb, (0.5, 2.0, 6.0))

    bf = _board_feats(tuple(state.board))
    return (hand, street, position, sb, ob, pb, tb, bf)


def encode_state(context: dict) -> Tuple:
    """
    Encode a loose context dict (tests / offline logs).

    Prefer encode_from_hand_state when a HandState is available.
    """
    return (
        context.get("hand", "UNKNOWN"),
        context.get("street", "preflop"),
        context.get("position", "UNKNOWN"),
        int(context.get("stack_bb", 0)),
        int(context.get("opp_stack_bb", 0)),
        float(context.get("to_call_bb", 0.0)),
        float(context.get("pot_bb", 0.0)),
        context.get("opponent_tendency", "Unknown"),
    )
