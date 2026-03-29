"""
Heads-up Texas Hold'em hand engine (in progress).

This module currently supports pre-flop betting and showdown, but it has been
refactored to be street-agnostic so it can be expanded to flop/turn/river betting.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Tuple

from full_game_engine.cards import Card, new_deck
from full_game_engine.hand_eval import compare_at_showdown

ActionKind = Literal["fold", "call", "check", "raise_to"]
Street = Literal["preflop", "flop", "turn", "river"]
Phase = Literal["preflop", "flop", "turn", "river", "showdown", "hand_over"]


@dataclass
class HandState:
    stacks: List[int]  # remaining chips before committing current street
    hole_cards: Tuple[Tuple[Card, Card], Tuple[Card, Card]]
    deck: List[Card]
    pot: int
    # Per-street betting state (for now, round_contrib/acted still refer to the *current* street).
    round_contrib: List[int]  # chips put in this betting round for current street
    acted: List[bool]  # voluntary action closed for this "chain" on current street
    last_raise_increment: int  # min-raise increment for current street
    actor: int  # 0 or 1
    phase: Phase
    street: Street  # current betting street (preflop/flop/turn/river)
    street_contrib: Dict[Street, List[int]]  # contributions by street
    street_acted: Dict[Street, List[bool]]  # acted flags by street
    board: List[Card]
    sb_chips: int
    bb_chips: int
    button: int  # who is BTN/SB this hand (0 or 1)
    winner: Optional[int]  # None until resolved; 0, 1, or -1 chop
    history: List[Dict[str, Any]] = field(default_factory=list)

    def max_bet(self) -> int:
        return max(self.round_contrib)

    def to_call(self, player: int) -> int:
        return self.max_bet() - self.round_contrib[player]

    def _other(self, p: int) -> int:
        return 1 - p


def _is_betting_phase(state: HandState) -> bool:
    return state.phase in {"preflop", "flop", "turn", "river"}


def _sync_current_street_views(state: HandState) -> None:
    """
    Ensure `round_contrib` / `acted` reflect the current street dictionaries.

    We keep `round_contrib` and `acted` for backwards compatibility, but the canonical
    per-street storage is `street_contrib` and `street_acted`.
    """
    state.round_contrib = state.street_contrib[state.street]
    state.acted = state.street_acted[state.street]


def _round_closed(state: HandState) -> bool:
    """
    A betting round is closed when:
    - both players have acted in the current "chain", and
    - their contributions for the street are equal (no one is facing a bet).
    """
    return bool(state.acted[0] and state.acted[1] and state.round_contrib[0] == state.round_contrib[1])


def _first_to_act_postflop(state: HandState) -> int:
    """In heads-up, first to act post-flop is the player out of position (non-button)."""
    return 1 - state.button


def _reset_street_betting(state: HandState) -> None:
    """Reset per-street betting trackers for the current street."""
    state.street_contrib[state.street] = [0, 0]
    state.street_acted[state.street] = [False, False]
    state.last_raise_increment = state.bb_chips
    _sync_current_street_views(state)


def _deal_to_board(state: HandState, n_cards: int) -> None:
    """Deal until board has n_cards (no burn card)."""
    while len(state.board) < n_cards:
        state.board.append(state.deck.pop())


def _advance_street(state: HandState) -> None:
    """
    Advance to the next street after a betting round closes.
    Preflop -> Flop -> Turn -> River -> Showdown.
    """
    if state.street == "preflop":
        state.street = "flop"
        state.phase = "flop"
        _deal_to_board(state, 3)
        _reset_street_betting(state)
        state.actor = _first_to_act_postflop(state)
        state.history.append({"event": "street", "street": "flop", "board": [str(c) for c in state.board]})
        return
    if state.street == "flop":
        state.street = "turn"
        state.phase = "turn"
        _deal_to_board(state, 4)
        _reset_street_betting(state)
        state.actor = _first_to_act_postflop(state)
        state.history.append({"event": "street", "street": "turn", "board": [str(c) for c in state.board]})
        return
    if state.street == "turn":
        state.street = "river"
        state.phase = "river"
        _deal_to_board(state, 5)
        _reset_street_betting(state)
        state.actor = _first_to_act_postflop(state)
        state.history.append({"event": "street", "street": "river", "board": [str(c) for c in state.board]})
        return
    if state.street == "river":
        _go_showdown(state)
        return


def _runout_to_showdown(state: HandState) -> None:
    """
    If a player is all-in, deal remaining streets with no further actions and go to showdown.
    """
    _deal_to_board(state, 5)
    _go_showdown(state)


def _post_blinds(
    stacks: List[int],
    sb: int,
    bb: int,
    button: int,
) -> Tuple[int, List[int], List[int]]:
    """Button posts SB, other posts BB. Returns (pot, new stacks, new contrib)."""
    bb_seat = 1 - button
    s = stacks.copy()
    c = [0, 0]
    # Short stacks post all-in for whatever they have, never below zero.
    post_sb = min(max(s[button], 0), sb)
    post_bb = min(max(s[bb_seat], 0), bb)
    s[button] -= post_sb
    s[bb_seat] -= post_bb
    c[button] = post_sb
    c[bb_seat] = post_bb
    pot = post_sb + post_bb
    return pot, s, c


def new_hand(
    stacks: List[int],
    rng: Optional[random.Random] = None,
    button: int = 0,
    sb_chips: int = 10,
    bb_chips: int = 20,
) -> HandState:
    """Start a new hand. stacks are total chips per player (before posting blinds)."""
    r = rng or random.Random()
    deck = new_deck(r)
    h0 = (deck.pop(), deck.pop())
    h1 = (deck.pop(), deck.pop())

    pot, stacks_after, contrib = _post_blinds(stacks, sb_chips, bb_chips, button)

    state = HandState(
        stacks=stacks_after,
        hole_cards=(h0, h1),
        deck=deck,
        pot=pot,
        round_contrib=contrib,
        acted=[False, False],
        last_raise_increment=bb_chips,
        actor=button,
        phase="preflop",
        street="preflop",
        street_contrib={
            "preflop": contrib.copy(),
            "flop": [0, 0],
            "turn": [0, 0],
            "river": [0, 0],
        },
        street_acted={
            "preflop": [False, False],
            "flop": [False, False],
            "turn": [False, False],
            "river": [False, False],
        },
        board=[],
        sb_chips=sb_chips,
        bb_chips=bb_chips,
        button=button,
        winner=None,
        history=[{"event": "deal", "button": button, "sb": sb_chips, "bb": bb_chips}],
    )
    _sync_current_street_views(state)
    return state


def legal_actions(state: HandState) -> List[Dict[str, Any]]:
    """Return list of legal action dicts for current actor."""
    if not _is_betting_phase(state):
        return []
    _sync_current_street_views(state)
    p = state.actor
    tc = state.to_call(p)
    stack = state.stacks[p]
    cur = state.round_contrib[p]
    mb = state.max_bet()
    out: List[Dict[str, Any]] = []

    if tc > 0:
        out.append({"kind": "fold"})
        # In no-limit, you may call all-in for less than the full amount to call.
        pay = min(tc, stack)
        if pay > 0:
            out.append({"kind": "call", "amount": pay})

    if tc == 0:
        out.append({"kind": "check"})

    # Raises: total contribution this round after raise
    min_raise_to = mb + state.last_raise_increment
    need = min_raise_to - cur
    if need <= stack and min_raise_to > cur:
        candidates = {min_raise_to}
        for mult in (3, 4, 5, 6):
            total = mult * state.bb_chips
            if total >= min_raise_to and total - cur <= stack:
                candidates.add(total)
        for total in sorted(candidates):
            if total > cur and total - cur <= stack:
                out.append({"kind": "raise_to", "total": total})

    return out


def raise_amount_range(state: HandState) -> Optional[Dict[str, int]]:
    """Inclusive chip totals (round contribution this street) for a legal raise."""
    if not _is_betting_phase(state):
        return None
    _sync_current_street_views(state)
    p = state.actor
    stack = state.stacks[p]
    cur = state.round_contrib[p]
    mb = state.max_bet()
    min_raise_to = mb + state.last_raise_increment
    need = min_raise_to - cur
    if need > stack or min_raise_to <= cur:
        return None
    max_total = cur + stack
    if max_total < min_raise_to:
        return None
    return {"min": min_raise_to, "max": max_total, "step": 1}


def apply_action(state: HandState, action: Dict[str, Any]) -> None:
    """Mutate state. action: kind fold|call|check|raise_to with optional total."""
    if not _is_betting_phase(state):
        raise ValueError("Not in a betting phase")
    _sync_current_street_views(state)
    p = state.actor
    kind: ActionKind = action["kind"]
    state.history.append({"player": p, "action": dict(action)})

    if kind == "fold":
        w = state._other(p)
        state.winner = w
        state.stacks[w] += state.pot
        state.pot = 0
        state.phase = "hand_over"
        return

    if kind == "check":
        if state.to_call(p) != 0:
            raise ValueError("Cannot check with amount to call")
        state.acted[p] = True
        if _round_closed(state):
            _advance_street(state)
        else:
            state.actor = state._other(p)
        return

    if kind == "call":
        tc = state.to_call(p)
        if tc <= 0:
            raise ValueError("Nothing to call")
        # Allow all-in calls for less than full to-call.
        pay = min(tc, state.stacks[p])
        if pay <= 0:
            raise ValueError("Not enough chips")
        state.stacks[p] -= pay
        state.pot += pay
        state.round_contrib[p] += pay
        state.acted[p] = True
        # If this was a short all-in call, refund the uncalled portion to the bettor
        # (side-pot is uncontested in heads-up and belongs to the covering player).
        if pay < tc:
            o = state._other(p)
            excess = state.round_contrib[o] - state.round_contrib[p]
            if excess > 0:
                state.round_contrib[o] -= excess
                state.pot -= excess
                state.stacks[o] += excess
                state.history.append({"event": "uncalled_return", "player": o, "amount": excess})
            _runout_to_showdown(state)
            return
        # If anyone is all-in after calling, run out to showdown.
        if state.stacks[0] == 0 or state.stacks[1] == 0:
            _runout_to_showdown(state)
            return
        if _round_closed(state):
            _advance_street(state)
        else:
            state.actor = state._other(p)
        return

    if kind == "raise_to":
        total = int(action["total"])
        old_max = state.max_bet()
        need_total = total - state.round_contrib[p]
        if need_total > state.stacks[p] or total < state.round_contrib[p]:
            raise ValueError("Invalid raise")
        if total < old_max + state.last_raise_increment:
            raise ValueError("Raise too small")
        state.stacks[p] -= need_total
        state.pot += need_total
        state.round_contrib[p] = total
        new_max = state.max_bet()
        state.last_raise_increment = max(new_max - old_max, state.bb_chips)
        state.acted[p] = True
        state.acted[state._other(p)] = False
        state.actor = state._other(p)
        # If the raiser is now all-in, the responder will still act (fold/call),
        # but if both end up all-in after response, the call branch will runout.
        return

    raise ValueError(f"Unknown action {kind}")


def _go_showdown(state: HandState) -> None:
    """Deal board and resolve winner."""
    # Ensure full board is dealt before showdown
    _deal_to_board(state, 5)
    state.phase = "showdown"
    h0, h1 = state.hole_cards
    cmp_ = compare_at_showdown(h0, h1, state.board)
    if cmp_ == 1:
        state.winner = 0
        state.stacks[0] += state.pot
    elif cmp_ == -1:
        state.winner = 1
        state.stacks[1] += state.pot
    else:
        state.winner = -1
        half = state.pot // 2
        state.stacks[0] += half
        state.stacks[1] += state.pot - half
    state.pot = 0
    state.phase = "hand_over"
    state.history.append(
        {
            "event": "showdown",
            "board": [str(c) for c in state.board],
            "winner": state.winner,
        }
    )


def random_legal_action(state: HandState, rng: random.Random) -> Dict[str, Any]:
    acts = legal_actions(state)
    return rng.choice(acts)

