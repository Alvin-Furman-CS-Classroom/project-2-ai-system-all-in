"""
Monte Carlo simulator for pre-flop opening actions.

Runs many simulated trials (random opponent actions and hand outcomes) to estimate
the value of an opening action. 
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple, Dict, Optional, List
import math
import random
import re


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

            base_equity = get_hand_equity(hand)
            equity = _effective_equity_vs_continuing_range(
                base_equity=base_equity,
                opponent_action="raise",
                opponent_tendency=opponent_tendency,
                bet_size=raise_to,
            )
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
    base_equity = get_hand_equity(hand)
    equity = _effective_equity_vs_continuing_range(
        base_equity=base_equity,
        opponent_action="call",
        opponent_tendency=opponent_tendency,
        bet_size=bet_size,
    )
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
) -> Dict:
    """
    Run num_trials Monte Carlo trials for (hand, action, bet_size) and return
    sample mean value, standard deviation, and 95% confidence interval.
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
