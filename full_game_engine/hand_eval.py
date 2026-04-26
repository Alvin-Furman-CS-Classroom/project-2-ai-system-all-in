"""Best 5 of 7 Hold'em hand evaluation. Returns comparable strength tuples (higher wins)."""

from __future__ import annotations

import itertools
from typing import List, Tuple

from full_game_engine.cards import Card

# Hand category: higher is better for category
_HIGH_CARD = 0
_PAIR = 1
_TWO_PAIR = 2
_TRIPS = 3
_STRAIGHT = 4
_FLUSH = 5
_FULL_HOUSE = 6
_QUADS = 7
_STRAIGHT_FLUSH = 8


def _rank_five(cards: List[Card]) -> Tuple[int, Tuple[int, ...]]:
    """Return (category, tiebreak tuple). Higher tuple wins."""
    ranks = sorted([c.rank for c in cards], reverse=True)
    suits = [c.suit for c in cards]
    rank_counts: dict[int, int] = {}
    for r in ranks:
        rank_counts[r] = rank_counts.get(r, 0) + 1
    counts = sorted(rank_counts.items(), key=lambda x: (x[1], x[0]), reverse=True)
    is_flush = len(set(suits)) == 1

    # Straight check (wheel: A-2-3-4-5 uses A as low)
    uniq = sorted(set(ranks), reverse=True)
    straight_high = -1
    if len(uniq) == 5:
        if uniq[0] - uniq[4] == 4:
            straight_high = uniq[0]
        # Wheel A-2-3-4-5 (ranks A=12, 5=3, 4=2, 3=1, 2=0)
        if set(ranks) == {12, 3, 2, 1, 0}:
            straight_high = 3  # 5-high straight; loses to 6-high

    is_straight = straight_high >= 0

    if is_flush and is_straight:
        return (_STRAIGHT_FLUSH, (straight_high,))

    if counts[0][1] == 4:
        quad_rank = counts[0][0]
        kicker = max(r for r in ranks if r != quad_rank)
        return (_QUADS, (quad_rank, kicker))

    if counts[0][1] == 3 and counts[1][1] == 2:
        return (_FULL_HOUSE, (counts[0][0], counts[1][0]))

    if is_flush:
        return (_FLUSH, tuple(ranks))

    if is_straight:
        return (_STRAIGHT, (straight_high,))

    if counts[0][1] == 3:
        trips = counts[0][0]
        kickers = sorted([r for r in ranks if r != trips], reverse=True)
        return (_TRIPS, (trips, kickers[0], kickers[1]))

    if counts[0][1] == 2 and counts[1][1] == 2:
        p1, p2 = sorted([counts[0][0], counts[1][0]], reverse=True)
        kicker = max(r for r in ranks if r not in (p1, p2))
        return (_TWO_PAIR, (p1, p2, kicker))

    if counts[0][1] == 2:
        pr = counts[0][0]
        ks = sorted([r for r in ranks if r != pr], reverse=True)
        return (_PAIR, (pr, ks[0], ks[1], ks[2]))

    return (_HIGH_CARD, tuple(ranks))


def best_hand_strength(hole: Tuple[Card, Card], board: List[Card]) -> Tuple[int, Tuple[int, ...]]:
    """Strength tuple for best 5-card hand from 7 cards."""
    seven = list(hole) + list(board)
    best: Tuple[int, Tuple[int, ...]] = (-1, ())
    for combo in itertools.combinations(seven, 5):
        cat, tb = _rank_five(list(combo))
        if (cat, tb) > best:
            best = (cat, tb)
    return best


def compare_at_showdown(
    hole0: Tuple[Card, Card],
    hole1: Tuple[Card, Card],
    board: List[Card],
) -> int:
    """Return 1 if player 0 wins, -1 if player 1 wins, 0 for chop."""
    s0 = best_hand_strength(hole0, board)
    s1 = best_hand_strength(hole1, board)
    if s0 > s1:
        return 1
    if s1 > s0:
        return -1
    return 0

