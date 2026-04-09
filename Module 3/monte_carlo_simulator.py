"""
Monte Carlo simulator for opening-action EV estimation.

Preflop equity comes from ``docs/POKER_HAND_WIN_PERCENTAGES.md``. When hole cards and
a non-empty board are supplied (e.g. full-game postflop), equity vs villain
continuation uses board-aware *conditioned* ranges (call vs raise) with importance
sampling instead of a single preflop discount heuristic.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Tuple, Dict, Optional, List, Any, Callable
import math
import random
import re

_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


# Opponent tendency base probability tables (fold, call, raise) for a "standard" open.
OPPONENT_PROBABILITIES: Dict[str, Dict[str, float]] = {
    "Tight": {"fold": 0.7, "call": 0.25, "raise": 0.05},
    "Loose": {"fold": 0.3, "call": 0.45, "raise": 0.25},
    "Aggressive": {"fold": 0.2, "call": 0.3, "raise": 0.5},
    "Passive": {"fold": 0.4, "call": 0.55, "raise": 0.05},
    "Unknown": {"fold": 0.4, "call": 0.4, "raise": 0.2},
}


def _normalize_hand_notation(hand: str) -> str:
    """
    Normalize hand notation to a compact form compatible with the equity table.
    Examples: "Ace-King suited" -> "AKs", "AA" -> "AA".
    """
    h = hand.strip()
    # Already in compact-ish form (we will canonicalize ordering below)
    if re.fullmatch(r"[2-9TJQKA]{2}[soSO]?", h):
        h = h.upper()
        if len(h) == 3:
            h = h[:2] + h[2].lower()
        # Canonicalize to "low card first" for non-pairs (equity table uses e.g. "KAs", "27o")
        r1, r2 = h[0], h[1]
        suffix = h[2:]  # "" or "s" or "o"
        rank_order = {r: i for i, r in enumerate("23456789TJQKA")}
        if r1 != r2 and rank_order.get(r1, 0) > rank_order.get(r2, 0):
            return f"{r2}{r1}{suffix}"
        return h

    rank_map = {
        "2": "2",
        "3": "3",
        "4": "4",
        "5": "5",
        "6": "6",
        "7": "7",
        "8": "8",
        "9": "9",
        "10": "T",
        "T": "T",
        "J": "J",
        "Q": "Q",
        "K": "K",
        "A": "A",
        "Ace": "A",
        "King": "K",
        "Queen": "Q",
        "Jack": "J",
    }

    parts = re.split(r"[\s\-]+", h)
    parts = [p for p in parts if p]
    if not parts:
        return h

    # Try to parse things like "Ace-King suited"
    if len(parts) >= 2:
        r1 = rank_map.get(parts[0], None)
        r2 = rank_map.get(parts[1], None)
        rest = " ".join(parts[2:]).lower() if len(parts) > 2 else ""
        if r1 and r2:
            if r1 == r2:
                return f"{r1}{r2}"
            if "suit" in rest:
                # Canonicalize to low card first
                rank_order = {r: i for i, r in enumerate("23456789TJQKA")}
                if rank_order.get(r1, 0) > rank_order.get(r2, 0):
                    r1, r2 = r2, r1
                return f"{r1}{r2}s"
            if "off" in rest:
                rank_order = {r: i for i, r in enumerate("23456789TJQKA")}
                if rank_order.get(r1, 0) > rank_order.get(r2, 0):
                    r1, r2 = r2, r1
                return f"{r1}{r2}o"
            rank_order = {r: i for i, r in enumerate("23456789TJQKA")}
            if rank_order.get(r1, 0) > rank_order.get(r2, 0):
                r1, r2 = r2, r1
            return f"{r1}{r2}"

    return h


def _load_hand_equity() -> Dict[str, float]:
    """
    Load hand equity (win percentage) from docs/POKER_HAND_WIN_PERCENTAGES.md.
    Falls back to an empty dict if the file is missing.
    """
    equity: Dict[str, float] = {}
    docs_path = Path(__file__).resolve().parent.parent / "docs" / "POKER_HAND_WIN_PERCENTAGES.md"
    if not docs_path.exists():
        return equity

    # Matches table rows like:
    # | 9 | KAs | 66.83% | Premium |
    pattern = re.compile(r"^\|\s*\d+\s*\|\s*([2-9TJQKA]{2}[so]?)\s*\|\s*([\d.]+)%")
    with docs_path.open("r", encoding="utf-8") as f:
        for line in f:
            match = pattern.match(line)
            if not match:
                continue
            hand, pct_str = match.group(1), match.group(2)
            try:
                pct = float(pct_str)
            except ValueError:
                continue
            equity[hand] = pct / 100.0
    return equity


HAND_EQUITY: Dict[str, float] = _load_hand_equity()


def get_hand_equity(hand: str) -> float:
    """
    Get approximate pre-flop equity for a hand from the equity table.
    Defaults to 0.5 (coin flip) if not found.
    """
    key = _normalize_hand_notation(hand)
    return HAND_EQUITY.get(key, 0.5)


def _effective_equity_vs_continuing_range(
    base_equity: float,
    opponent_action: str,
    opponent_tendency: str,
    bet_size: float,
) -> float:
    """
    Reduce hero equity when villain continues (calls/raises) to reflect that
    villain's continuing range is stronger than a random hand.

    This is a deliberately simple abstraction: we discount equity by a factor
    depending on (call vs raise), opponent tendency, and bet size pressure.
    """
    if opponent_action not in {"call", "raise"}:
        return base_equity

    # Base discounts (raise implies stronger range than call)
    k_call = 0.92
    k_raise = 0.78

    # Opponent-type adjustments: tighter opponents continue with stronger ranges.
    if opponent_tendency == "Tight":
        k_call -= 0.04
        k_raise -= 0.06
    elif opponent_tendency == "Loose":
        k_call += 0.02
        k_raise += 0.02
    elif opponent_tendency == "Passive":
        k_call -= 0.02
        k_raise -= 0.02
    # Aggressive: leave as base; aggression affects frequency more than range strength here.

    # Bet-size pressure: larger opens make continuing range stronger.
    adj = _bet_size_adjustment(max(bet_size, 0.0))  # ~0.5 at 3x
    k_call -= 0.05 * (adj - 0.5)
    k_raise -= 0.08 * (adj - 0.5)

    k = k_raise if opponent_action == "raise" else k_call
    k = max(0.3, min(1.0, k))
    eff = base_equity * k
    return max(0.0, min(1.0, eff))


def _logistic(x: float) -> float:
    """Standard logistic function."""
    return 1.0 / (1.0 + math.exp(-x))


def _bet_size_adjustment(bet_size: float) -> float:
    """
    Return an adjustment factor based on bet size using a logistic curve.

    We treat 3x as a "standard" open (no adjustment), with larger bets
    increasing fold probability and smaller bets reducing it.

    The returned value is in (0, 1) and centered near 0.5 around bet_size=3.
    We'll map this into a multiplier around 1.0.
    """
    # Center at 3x, scale controls how quickly adjustment changes with size.
    # Use a larger scale to make the effect of bet size gentler.
    scale = 2.0
    x = (bet_size - 3.0) / scale
    return _logistic(x)  # ~0.5 at 3x, >0.5 for larger, <0.5 for smaller


def _get_adjusted_opponent_probs(
    opponent_tendency: str,
    bet_size: float,
) -> Dict[str, float]:
    """
    Adjust base opponent probabilities using a logistic function of bet size.

    Intuition:
    - Larger bets → somewhat more folds, somewhat fewer calls.
    - Smaller bets → somewhat fewer folds, somewhat more calls.
    - Raise frequency is nudged upward for larger bets, especially vs Tight opponents.
    """
    base = OPPONENT_PROBABILITIES.get(opponent_tendency, OPPONENT_PROBABILITIES["Unknown"])
    adj = _bet_size_adjustment(bet_size)  # (0, 1)

    # Map adj in (0,1) to multipliers around 1.0, but keep the effect modest.
    # When adj > 0.5 (larger bet), fold_mult > 1; when adj < 0.5, fold_mult < 1.
    # 0.5 ± 0.5 → range [0, 1]; add 0.9 → approx [0.4, 1.4] but with gentle slope.
    fold_mult = 0.9 + 0.3 * (adj - 0.5)
    call_mult = 0.9 - 0.3 * (adj - 0.5)  # opposite effect for calls

    # Slightly increase raise frequency for larger bets, especially vs Tight.
    base_raise = base["raise"]
    if opponent_tendency == "Tight":
        raise_mult = 1.0 + 0.4 * (adj - 0.5)
    else:
        raise_mult = 1.0 + 0.2 * (adj - 0.5)

    fold = base["fold"] * fold_mult
    call = base["call"] * call_mult
    raise_p = base["raise"] * raise_mult

    total = fold + call + raise_p
    if total <= 0.0:
        return base

    return {
        "fold": fold / total,
        "call": call / total,
        "raise": raise_p / total,
    }


def _full_deck_cards() -> List[Any]:
    """All 52 cards as ``full_game_engine.cards.Card`` instances."""
    from full_game_engine.cards import Card

    return [Card(r, s) for r in range(13) for s in range(4)]


def monte_carlo_equity_vs_random_hand(
    hero_hole: Tuple[Any, Any],
    board: List[Any],
    rng: random.Random,
    num_samples: int,
) -> float:
    """
    Estimate hero equity (win rate + half chops) vs a uniformly random villain hand,
    with random completion of the board if fewer than five cards are known.

    Uses ``compare_at_showdown`` from the full-game engine so board texture matters.
    Hole/board cards are normalized to ``full_game_engine.cards.Card`` so deck exclusion
    works even when callers pass compatible card types from another package.

    Kept for diagnostics and comparisons; ``run_simulation`` postflop uses
    :func:`monte_carlo_equity_vs_conditioned_range` instead.
    """
    if num_samples <= 0:
        return 0.5
    from full_game_engine.cards import Card as FE_Card
    from full_game_engine.hand_eval import compare_at_showdown

    def _norm(c: Any) -> Any:
        return FE_Card(int(c.rank), int(c.suit))

    hero_hole = (_norm(hero_hole[0]), _norm(hero_hole[1]))
    board = [_norm(c) for c in board]

    wins = 0.0
    done = 0
    for _ in range(num_samples):
        used = {hero_hole[0], hero_hole[1], *board}
        deck = [c for c in _full_deck_cards() if c not in used]
        rng.shuffle(deck)
        if len(deck) < 2:
            break
        v0, v1 = deck[0], deck[1]
        rest = deck[2:]
        full_board = list(board)
        need = 5 - len(full_board)
        if need > 0:
            if len(rest) < need:
                break
            full_board.extend(rest[:need])
        cmp_ = compare_at_showdown(hero_hole, (v0, v1), full_board)
        done += 1
        if cmp_ == 1:
            wins += 1.0
        elif cmp_ == 0:
            wins += 0.5
    return wins / done if done > 0 else 0.5


def _norm_fe_card(c: Any) -> Any:
    from full_game_engine.cards import Card as FE_Card

    return FE_Card(int(c.rank), int(c.suit))


def _villain_hand_postflop_score(hole: Tuple[Any, Any], board: List[Any]) -> float:
    """
    Map villain hole + board to [0, 1] for soft range weighting (made strength + draws).
    """
    from full_game_engine.hand_eval import best_hand_strength

    if len(board) < 3:
        return 0.5
    cat, _tb = best_hand_strength(hole, board)
    s = cat / 8.0
    allc = list(hole) + list(board)
    for suit in range(4):
        cnt = sum(1 for c in allc if c.suit == suit)
        if cnt >= 4:
            s += 0.09
        elif cnt == 3:
            s += 0.045
    ranks = sorted([c.rank for c in allc], reverse=True)
    uniq = sorted(set(ranks), reverse=True)
    if len(uniq) >= 4:
        for i in range(len(uniq) - 3):
            window = uniq[i : i + 4]
            if len(window) == 4 and window[0] - window[3] == 3:
                s += 0.05
                break
    return max(0.0, min(1.0, s))


def _continuing_range_weight(
    score: float,
    villain_mode: str,
    opponent_tendency: str,
    bet_size: float,
) -> float:
    """
    Soft weight for including a villain hand in call vs raise continuing ranges.
    Raise ranges concentrate on higher scores; larger bets tighten both.
    """
    adj = _bet_size_adjustment(max(bet_size, 0.25))
    pressure = 0.25 + 0.75 * adj
    tight = {
        "Tight": 1.12,
        "Loose": 0.88,
        "Aggressive": 0.94,
        "Passive": 1.06,
        "Unknown": 1.0,
    }.get(opponent_tendency, 1.0)
    t_call = (0.26 + 0.1 * pressure) * tight
    t_raise = (0.48 + 0.12 * pressure) * tight
    if villain_mode == "call":
        return max(1e-9, _logistic(8.0 * (score - t_call)))
    if villain_mode == "raise":
        return max(1e-9, _logistic(10.5 * (score - t_raise)))
    return max(1e-9, _logistic(8.0 * (score - t_call)))


def monte_carlo_equity_vs_conditioned_range(
    hero_hole: Tuple[Any, Any],
    board: List[Any],
    villain_mode: str,
    opponent_tendency: str,
    bet_size: float,
    rng: random.Random,
    num_samples: int,
) -> float:
    """
    Hero equity vs a board-aware *conditioned* villain range (call or raise),
    using importance sampling: uniform villain holes weighted by
    ``_continuing_range_weight`` on a simple postflop strength score.
    """
    from full_game_engine.hand_eval import compare_at_showdown

    if num_samples <= 0:
        return 0.5
    hero_hole = (_norm_fe_card(hero_hole[0]), _norm_fe_card(hero_hole[1]))
    board = [_norm_fe_card(c) for c in board]

    used = {hero_hole[0], hero_hole[1], *board}
    deck = [c for c in _full_deck_cards() if c not in used]
    n = len(deck)
    if n < 2:
        return 0.5

    sum_w = 0.0
    sum_wx = 0.0
    done = 0
    for _ in range(num_samples):
        ia, ib = rng.sample(range(n), 2)
        v0, v1 = deck[ia], deck[ib]
        hole_v = (v0, v1)
        sc = _villain_hand_postflop_score(hole_v, board)
        w = _continuing_range_weight(
            sc, villain_mode, opponent_tendency, bet_size
        )
        remaining = [c for c in deck if c not in hole_v]
        rng.shuffle(remaining)
        full_board = list(board)
        need = 5 - len(full_board)
        if need > 0:
            if len(remaining) < need:
                break
            full_board.extend(remaining[:need])
        cmp_ = compare_at_showdown(hero_hole, hole_v, full_board)
        done += 1
        if cmp_ == 1:
            x = 1.0
        elif cmp_ == 0:
            x = 0.5
        else:
            x = 0.0
        sum_w += w
        sum_wx += w * x
    return sum_wx / sum_w if sum_w > 0 and done > 0 else 0.5


def _sample_opponent_action(
    opponent_tendency: str,
    bet_size: float,
    rng: random.Random,
) -> str:
    """
    Sample opponent response (fold / call / raise) given their tendency
    and our bet size, using a logistic adjustment so that larger bets
    induce more folds and smaller bets induce more calls.
    """
    probs = _get_adjusted_opponent_probs(opponent_tendency, bet_size)
    r = rng.random()
    cumulative = 0.0
    for action, p in probs.items():
        cumulative += p
        if r <= cumulative:
            return action
    return "call"


def run_trial(
    hand: str,
    action: str,
    bet_size: float,
    position: str,
    stack_sizes: Tuple[int, int],
    opponent_tendency: str,
    pot_size: float = 1.5,
    rng: Optional[random.Random] = None,
    equity_override: Optional[float] = None,
    postflop_equity_getter: Optional[Callable[[str, float], float]] = None,
) -> float:
    """
    Run a single Monte Carlo trial for a given opening action.

    Value model:
    - If we fold pre-flop, payoff is 0 (baseline).
    - If we open and villain folds, we win the existing pot (pot_size).
    - If we open and villain calls, we go to showdown:
      - Total pot at showdown ≈ pot_size + 2 * bet_size.
      - If we win, payoff = total_pot - our_investment = pot_size + bet_size.
      - If we lose, payoff = -bet_size.
      Outcome is sampled using approximate hand equity.
    - If villain raises, we simulate a simple raise-to size and decide whether to call
      based on pot odds vs hand equity. If we call, we go to showdown for the raised pot.
    """
    if rng is None:
        rng = random.Random()

    if action == "fold" or bet_size <= 0.0:
        return 0.0

    def _base_equity() -> float:
        if equity_override is not None:
            return float(equity_override)
        return get_hand_equity(hand)

    def _equity_vs_continue(
        opponent_action: str,
        size_bb: float,
        base: float,
    ) -> float:
        """Preflop: discount vs continuing range. Postflop: use conditioned MC equity only."""
        if postflop_equity_getter is not None:
            mode = "raise" if opponent_action == "raise" else "call"
            return float(postflop_equity_getter(mode, size_bb))
        return _effective_equity_vs_continuing_range(
            base_equity=base,
            opponent_action=opponent_action,
            opponent_tendency=opponent_tendency,
            bet_size=size_bb,
        )

    # Sample opponent response with bet-size–dependent probabilities
    opponent_action = _sample_opponent_action(opponent_tendency, bet_size, rng)

    if opponent_action == "fold":
        # We pick up the pot uncontested
        return pot_size

    if opponent_action == "raise":
        # Simple model: villain raises to ~3x our open (capped by stacks),
        # hero calls if hand equity meets pot-odds threshold.
        your_stack, opp_stack = stack_sizes
        raise_to = min(3.0 * bet_size, float(your_stack), float(opp_stack))

        # If raise_to is not actually larger (e.g., very short stacks), treat as call.
        if raise_to <= bet_size + 1e-9:
            opponent_action = "call"
        else:
            call_additional = raise_to - bet_size
            # Pot after villain raises (before hero calls): pot_size + hero_open + villain_raise_to
            pot_before_call = pot_size + bet_size + raise_to
            # If hero calls, final pot becomes: pot_before_call + call_additional = pot_size + 2*raise_to
            required_equity = call_additional / (pot_before_call + call_additional)

            base_equity = _base_equity()
            equity = _equity_vs_continue("raise", raise_to, base_equity)
            if equity < required_equity:
                # Fold to the raise: lose our open
                return -bet_size

            # Call the raise and go to showdown at the raised size
            total_pot = pot_size + 2.0 * raise_to
            win_payoff = total_pot - raise_to
            lose_payoff = -raise_to
            if rng.random() < equity:
                return win_payoff
            return lose_payoff

    # Call: go to showdown
    base_equity = _base_equity()
    equity = _equity_vs_continue("call", bet_size, base_equity)
    total_pot = pot_size + 2.0 * bet_size
    win_payoff = total_pot - bet_size  # profit relative to starting stack
    lose_payoff = -bet_size

    if rng.random() < equity:
        return win_payoff
    return lose_payoff


def run_simulation(
    hand: str,
    action: str,
    bet_size: float,
    position: str,
    stack_sizes: Tuple[int, int],
    opponent_tendency: str,
    num_trials: int = 1000,
    pot_size: float = 1.5,
    seed: Optional[int] = None,
    hero_hole: Optional[Tuple[Any, Any]] = None,
    board: Optional[List[Any]] = None,
) -> Dict:
    """
    Run num_trials Monte Carlo trials for (hand, action, bet_size) and return
    sample mean value, standard deviation, and 95% confidence interval.

    When ``hero_hole`` and ``board`` are provided and ``board`` is non-empty,
    equity uses board-aware *conditioned* villain ranges for call vs raise
    (importance sampling), with per-(mode,bet_size) caching inside this run.
    """
    if num_trials <= 0:
        return {
            "value_estimate": 0.0,
            "std": 0.0,
            "confidence_interval": (0.0, 0.0),
            "num_trials": 0,
        }

    rng = random.Random(seed)
    values: List[float] = []

    postflop_equity_getter: Optional[Callable[[str, float], float]] = None
    if hero_hole is not None and board is not None and len(board) > 0:
        cache: Dict[Tuple[str, float], float] = {}

        def postflop_equity_getter_fn(mode: str, bs: float) -> float:
            key = (mode, round(float(bs), 4))
            if key not in cache:
                if mode == "call":
                    n_s = min(48, max(14, num_trials))
                else:
                    n_s = min(56, max(18, num_trials + 8))
                cache[key] = monte_carlo_equity_vs_conditioned_range(
                    hero_hole,
                    list(board),
                    villain_mode=mode,
                    opponent_tendency=opponent_tendency,
                    bet_size=float(bs),
                    rng=rng,
                    num_samples=n_s,
                )
            return cache[key]

        postflop_equity_getter = postflop_equity_getter_fn

    for _ in range(num_trials):
        v = run_trial(
            hand=hand,
            action=action,
            bet_size=bet_size,
            position=position,
            stack_sizes=stack_sizes,
            opponent_tendency=opponent_tendency,
            pot_size=pot_size,
            rng=rng,
            equity_override=None,
            postflop_equity_getter=postflop_equity_getter,
        )
        values.append(v)

    mean = sum(values) / num_trials
    if num_trials > 1:
        var = sum((v - mean) ** 2 for v in values) / (num_trials - 1)
        std = math.sqrt(var)
    else:
        std = 0.0

    # 95% confidence interval using normal approximation
    if num_trials > 1:
        margin = 1.96 * std / math.sqrt(num_trials)
    else:
        margin = 0.0
    ci = (mean - margin, mean + margin)

    return {
        "value_estimate": mean,
        "std": std,
        "confidence_interval": ci,
        "num_trials": num_trials,
    }


def run_simulation_for_strategy(
    strategy: Dict[str, float],
    position: str,
    stack_sizes: Tuple[int, int],
    opponent_tendency: str,
    num_trials_per_hand: int = 500,
    hands: Optional[List[str]] = None,
    seed: Optional[int] = None,
) -> Dict:
    """
    Run Monte Carlo simulation for an entire strategy (hand -> opening bet size;
    0.0 denotes fold). Returns overall value estimate and per-hand statistics.
    """
    if hands is None:
        hands = list(strategy.keys())

    rng = random.Random(seed)
    per_hand_results: Dict[str, Dict] = {}
    values: List[float] = []

    for hand in hands:
        bet_size = strategy.get(hand, 0.0)
        action = "fold" if bet_size <= 0.0 else "open"

        # Use independent seeds per hand for reproducibility
        hand_seed = rng.randint(0, 2**31 - 1)
        result = run_simulation(
            hand=hand,
            action=action,
            bet_size=bet_size,
            position=position,
            stack_sizes=stack_sizes,
            opponent_tendency=opponent_tendency,
            num_trials=num_trials_per_hand,
            pot_size=1.5,
            seed=hand_seed,
        )
        per_hand_results[hand] = {
            "action": action,
            "bet_size": bet_size,
            **result,
        }
        values.append(result["value_estimate"])

    if values:
        overall_mean = sum(values) / len(values)
        if len(values) > 1:
            var = sum((v - overall_mean) ** 2 for v in values) / (len(values) - 1)
            overall_std = math.sqrt(var)
            margin = 1.96 * overall_std / math.sqrt(len(values))
        else:
            overall_std = 0.0
            margin = 0.0
        overall_ci = (overall_mean - margin, overall_mean + margin)
    else:
        overall_mean = 0.0
        overall_std = 0.0
        overall_ci = (0.0, 0.0)

    return {
        "expected_value": overall_mean,
        "std": overall_std,
        "confidence_interval": overall_ci,
        "per_hand_results": per_hand_results,
        "num_hands": len(hands),
        "num_trials_per_hand": num_trials_per_hand,
    }
