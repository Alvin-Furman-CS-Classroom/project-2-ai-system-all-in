"""Deck and card utilities for Hold'em."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Optional, Tuple

RANKS = "23456789TJQKA"
SUITS = "cdhs"


@dataclass(frozen=True, order=True)
class Card:
    """Single card: rank index 0..12 (2..A), suit 0..3."""

    rank: int
    suit: int

    @classmethod
    def from_str(cls, s: str) -> "Card":
        s = s.strip()
        if len(s) != 2:
            raise ValueError(f"Bad card string: {s!r}")
        rch, sch = s[0], s[1].lower()
        if rch not in RANKS:
            raise ValueError(f"Bad rank: {rch}")
        if sch not in SUITS:
            raise ValueError(f"Bad suit: {sch}")
        return cls(RANKS.index(rch), SUITS.index(sch))

    def __str__(self) -> str:
        return f"{RANKS[self.rank]}{SUITS[self.suit]}"

    def to_display(self) -> str:
        rank_names = "23456789TJQKA"
        suit_symbols = {"c": "♣", "d": "♦", "h": "♥", "s": "♠"}
        return f"{rank_names[self.rank]}{suit_symbols[SUITS[self.suit]]}"


def new_deck(rng: Optional[random.Random] = None) -> List[Card]:
    deck = [Card(r, s) for r in range(13) for s in range(4)]
    r = rng or random.Random()
    r.shuffle(deck)
    return deck
