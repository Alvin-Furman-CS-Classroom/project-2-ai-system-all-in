"""
Heads-up Texas Hold'em: pre-flop betting only, then full board runout for showdown.

Conventions:
- Player 0 = Button / Small Blind; Player 1 = Big Blind.
- SB and BB in chip units (BB_CHIPS = 20, SB_CHIPS = 10 by default).
- Limp = call the difference to match the big blind (BTN completes).
- After pre-flop closes with both players in, deal 5 board cards and evaluate.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Tuple

from game_engine.cards import Card, new_deck
from game_engine.hand_eval import compare_at_showdown

ActionKind = Literal["fold", "call", "check", "raise_to"]


@dataclass
class HandState:
    stacks: List[int]  # remaining chips before committing current street
    hole_cards: Tuple[Tuple[Card, Card], Tuple[Card, Card]]
    deck: List[Card]
    pot: int
    round_contrib: List[int]  # chips put in this pre-flop round
    acted: List[bool]  # voluntary action closed for this "chain"
    last_raise_increment: int
    actor: int  # 0 or 1
    phase: Literal["preflop", "showdown", "hand_over"]
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


def _post_blinds(
    stacks: List[int],
    round_contrib: List[int],
    sb: int,
    bb: int,
    button: int,
) -> Tuple[int, int, List[int], List[int]]:
    """Button posts SB, other posts BB. Returns (pot, new stacks, new contrib)."""
    bb_seat = 1 - button
    s = stacks.copy()
    c = [0, 0]
    s[button] -= sb
    s[bb_seat] -= bb
    c[button] = sb
    c[bb_seat] = bb
    pot = sb + bb
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

    pot, stacks_after, contrib = _post_blinds(stacks, [0, 0], sb_chips, bb_chips, button)

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
        board=[],
        sb_chips=sb_chips,
        bb_chips=bb_chips,
        button=button,
        winner=None,
        history=[{"event": "deal", "button": button, "sb": sb_chips, "bb": bb_chips}],
    )
    return state


def legal_actions(state: HandState) -> List[Dict[str, Any]]:
    """Return list of legal action dicts for current actor."""
    if state.phase != "preflop":
        return []
    p = state.actor
    tc = state.to_call(p)
    stack = state.stacks[p]
    cur = state.round_contrib[p]
    mb = state.max_bet()
    out: List[Dict[str, Any]] = []

    if tc > 0:
        out.append({"kind": "fold"})
        if stack >= tc:
            out.append({"kind": "call", "amount": tc})
        # all-in call not implemented for v1

    if tc == 0:
        out.append({"kind": "check"})

    # Raises: total contribution this round after raise
    min_raise_to = mb + state.last_raise_increment
    # Must be able to put in min_raise_to total this round
    need = min_raise_to - cur
    if need <= stack and min_raise_to > cur:
        # Discrete sizes: min raise, 3bb, 4bb, 5bb (in chips: multiples of bb_chips)
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
    """
    Inclusive chip totals (round contribution this street) for a legal raise.
    None if raising is impossible (e.g. short stack cannot min-raise).
    """
    if state.phase != "preflop":
        return None
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


def apply_action(
    state: HandState,
    action: Dict[str, Any],
    *,
    decision_meta: Optional[Dict[str, Any]] = None,
) -> None:
    """Mutate state. action: kind fold|call|check|raise_to with optional total.

    Optional ``decision_meta`` (e.g. LLM reason/model) is stored on this history entry
    under key ``llm`` for post-hand review in the UI.
    """
    if state.phase != "preflop":
        raise ValueError("Not in preflop")
    p = state.actor
    kind: ActionKind = action["kind"]
    entry: Dict[str, Any] = {"player": p, "action": dict(action)}
    if decision_meta is not None:
        entry["llm"] = decision_meta
    state.history.append(entry)

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
        if state.acted[0] and state.acted[1] and state.round_contrib[0] == state.round_contrib[1]:
            _go_showdown(state)
        else:
            state.actor = state._other(p)
        return

    if kind == "call":
        tc = state.to_call(p)
        if tc <= 0:
            raise ValueError("Nothing to call")
        if state.stacks[p] < tc:
            raise ValueError("Not enough chips")
        state.stacks[p] -= tc
        state.pot += tc
        state.round_contrib[p] += tc
        state.acted[p] = True
        if state.acted[0] and state.acted[1] and state.round_contrib[0] == state.round_contrib[1]:
            _go_showdown(state)
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
        return

    raise ValueError(f"Unknown action {kind}")


def _go_showdown(state: HandState) -> None:
    """Deal board and resolve winner."""
    d = state.deck
    state.board = [d.pop() for _ in range(5)]
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
