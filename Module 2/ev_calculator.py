"""
Expected Value (EV) calculation for poker bet sizing.
Calculates the expected value of a bet size given hand, position, stack sizes, and opponent tendency.
"""

import sys
from pathlib import Path
from typing import Tuple, Optional
import re

# Add parent directory to path to access docs
sys.path.insert(0, str(Path(__file__).parent.parent))

# Opponent tendency probability tables
# Probabilities of opponent actions (fold, call, raise) given our bet size
OPPONENT_PROBABILITIES = {
    "Tight": {
        "fold": 0.70,  # Tight players fold more often
        "call": 0.25,
        "raise": 0.05
    },
    "Loose": {
        "fold": 0.30,  # Loose players call/raise more
        "call": 0.45,
        "raise": 0.25
    },
    "Aggressive": {
        "fold": 0.20,  # Aggressive players raise frequently
        "call": 0.30,
        "raise": 0.50
    },
    "Passive": {
        "fold": 0.40,  # Passive players call more, raise less
        "call": 0.55,
        "raise": 0.05
    },
    "Unknown": {
        "fold": 0.40,  # Default balanced probabilities
        "call": 0.40,
        "raise": 0.20
    }
}

# Base pot size for heads-up pre-flop (small blind + big blind)
BASE_POT_SIZE = 1.5  # 0.5 BB small blind + 1 BB big blind


def load_hand_equity() -> dict[str, float]:
    """
    Load hand equity (win percentage) from POKER_HAND_WIN_PERCENTAGES.md.
    
    Returns:
        Dictionary mapping hand notation (e.g., "AA", "KAs") to win percentage (0.0 to 1.0).
    """
    equity_dict = {}
    docs_path = Path(__file__).parent.parent / "docs" / "POKER_HAND_WIN_PERCENTAGES.md"
    
    try:
        with open(docs_path, 'r') as f:
            lines = f.readlines()
        
        # Parse the markdown table (starts around line 18)
        for line in lines[17:186]:  # Table rows
            match = re.match(r'\|\s*\d+\s*\|\s*([^\s|]+)\s*\|\s*([\d.]+)%', line)
            if match:
                hand = match.group(1)
                win_pct = float(match.group(2))
                equity_dict[hand] = win_pct / 100.0  # Convert to 0.0-1.0
        
    except FileNotFoundError:
        print(f"Warning: Could not find {docs_path}. Using empty equity dictionary.")
    
    return equity_dict


# Load hand equity data once at module import
HAND_EQUITY = load_hand_equity()


def normalize_hand(hand: str) -> Optional[str]:
    """
    Normalize hand notation to match HAND_EQUITY keys.
    
    Args:
        hand: Hand notation (e.g., "AKs", "Ace-King suited", "AA")
    
    Returns:
        Normalized hand notation or None if invalid.
    """
    h = hand.strip()
    
    # Check exact match first
    if h in HAND_EQUITY:
        return h
    
    # Common aliases
    key = h.replace("-", " ").replace("  ", " ").lower()
    aliases = {
        "ace king suited": "KAs", "ace-king suited": "KAs", "aks": "KAs",
        "ace king offsuit": "KAo", "ace-king offsuit": "KAo", "ako": "KAo",
        "pocket aces": "AA", "aces": "AA", "aa": "AA",
        "kings": "KK", "queens": "QQ", "jj": "JJ",
    }
    
    if key in aliases:
        return aliases[key]
    if h in aliases:
        return aliases[h]
    
    # Try two-char + s/o
    if len(h) >= 2:
        two = (h[0] + h[1]).upper()
        rest = h[2:].strip().lower()
        
        # Check if reversed (e.g., "AKs" -> "KAs")
        if len(two) == 2:
            reversed_two = two[1] + two[0]
            if reversed_two + "s" in HAND_EQUITY and rest in ("s", "suit", "suited", ""):
                return reversed_two + "s"
            if reversed_two + "o" in HAND_EQUITY and rest in ("o", "off", "offsuit", ""):
                return reversed_two + "o"
        
        if two + "s" in HAND_EQUITY and rest in ("s", "suit", "suited", ""):
            return two + "s"
        if two + "o" in HAND_EQUITY and rest in ("o", "off", "offsuit", ""):
            return two + "o"
        if two in HAND_EQUITY and (rest == "" or "pair" in rest):
            return two
    
    return None


def get_hand_equity(hand: str) -> float:
    """
    Get hand equity (win percentage) for a given hand.
    
    Args:
        hand: Hand notation
    
    Returns:
        Equity as float (0.0 to 1.0), or 0.5 if hand not found (default to coin flip).
    """
    normalized = normalize_hand(hand)
    if normalized and normalized in HAND_EQUITY:
        return HAND_EQUITY[normalized]
    return 0.5  # Default to 50% if hand not found


def calculate_ev(
    bet_size: float,
    hand: str,
    position: str,
    stack_sizes: Tuple[int, int],
    opponent_tendency: str,
    pot_size: float = BASE_POT_SIZE,
    opponent_bet_size: Optional[float] = None,
    action: str = "open"
) -> float:
    """
    Calculate expected value (EV) of a bet size or action.
    
    Handles two scenarios:
    1. Opening action (Button): bet_size is our opening raise size
    2. Facing a bet (Big Blind): opponent_bet_size is opponent's bet, action is "call" or "raise"
    
    Formula:
        EV = (fold_prob × pot_won) + (call_prob × [equity × total_pot - (1-equity) × bet_size]) + (raise_prob × ev_vs_raise)
    
    Args:
        bet_size: Bet size in big blinds
            - Opening action: our raise size (e.g., 3.0 for 3x BB)
            - Facing bet + call: amount to call (should equal opponent_bet_size)
            - Facing bet + raise: our total raise size (e.g., 5.0 for 5x BB total)
        hand: Starting hand notation (e.g., "AA", "AKs")
        position: Position ("Button" or "Big Blind")
        stack_sizes: Tuple of (your_stack, opponent_stack) in big blinds
        opponent_tendency: Opponent tendency ("Tight", "Loose", "Aggressive", "Passive", "Unknown")
        pot_size: Current pot size in big blinds (default: 1.5 for heads-up pre-flop)
        opponent_bet_size: Opponent's bet size if facing a bet (None for opening action)
        action: Action type - "open" (opening raise), "call" (call opponent's bet), or "raise" (re-raise)
    
    Returns:
        Expected value in big blinds.
    """
    your_stack, opponent_stack = stack_sizes
    
    # Handle facing a bet scenario
    if opponent_bet_size is not None:
        if action == "call":
            # Calling: we match opponent's bet
            our_investment = opponent_bet_size
            pot_size = pot_size + opponent_bet_size  # Opponent's bet is already in pot
        elif action == "raise":
            # Raising: bet_size is our total raise size
            our_investment = bet_size
            pot_size = pot_size + opponent_bet_size  # Opponent's bet is already in pot
        else:
            raise ValueError(f"Invalid action '{action}' when facing a bet. Use 'call' or 'raise'.")
    else:
        # Opening action: bet_size is our raise
        our_investment = bet_size
    
    # Cap investment at available stack
    our_investment = min(our_investment, your_stack)
    if our_investment <= 0:
        return 0.0
    
    # Get opponent action probabilities
    # Note: These probabilities may need adjustment based on bet sizing
    # (e.g., larger bets = more folds), but keeping simple for now
    opp_probs = OPPONENT_PROBABILITIES.get(
        opponent_tendency.strip(),
        OPPONENT_PROBABILITIES["Unknown"]
    )
    fold_prob = opp_probs["fold"]
    call_prob = opp_probs["call"]
    raise_prob = opp_probs["raise"]
    
    # Get hand equity
    equity = get_hand_equity(hand)
    
    # EV component 1: Opponent folds
    # We win the pot without further investment
    ev_fold = fold_prob * pot_size
    
    # EV component 2: Opponent calls
    # Total pot if called = current pot + our investment + opponent's matching call
    if opponent_bet_size is not None and action == "call":
        # We're calling, opponent already bet, so they just call our call (no additional)
        total_pot_if_called = pot_size + our_investment
    elif opponent_bet_size is not None and action == "raise":
        # We're raising, opponent calls our raise
        total_pot_if_called = pot_size + our_investment + (our_investment - opponent_bet_size)
    else:
        # Opening action: opponent calls our bet
        total_pot_if_called = pot_size + our_investment + our_investment
    
    # EV if called: equity × total_pot - our_investment
    ev_call = call_prob * (equity * total_pot_if_called - our_investment)
    
    # EV component 3: Opponent raises (re-raises us)
    # Simplified: we fold to the re-raise, losing our investment
    # (In reality, this could lead to 3-bet scenarios, but simplified for now)
    ev_raise = raise_prob * (-our_investment)
    
    # Total EV
    total_ev = ev_fold + ev_call + ev_raise
    
    return total_ev


def calculate_ev_for_bet_sizes(
    bet_sizes: list[float],
    hand: str,
    position: str,
    stack_sizes: Tuple[int, int],
    opponent_tendency: str,
    pot_size: float = BASE_POT_SIZE,
    opponent_bet_size: Optional[float] = None,
    action: str = "open"
) -> list[Tuple[float, float]]:
    """
    Calculate EV for multiple bet sizes or actions.
    
    Args:
        bet_sizes: List of bet sizes to evaluate
        hand: Starting hand notation
        position: Position
        stack_sizes: Tuple of (your_stack, opponent_stack)
        opponent_tendency: Opponent tendency
        pot_size: Current pot size
        opponent_bet_size: Opponent's bet size if facing a bet (None for opening action)
        action: Action type - "open", "call", or "raise"
    
    Returns:
        List of tuples (bet_size, ev) sorted by EV descending.
    """
    results = []
    for bet_size in bet_sizes:
        ev = calculate_ev(
            bet_size, hand, position, stack_sizes, opponent_tendency,
            pot_size, opponent_bet_size, action
        )
        results.append((bet_size, ev))
    
    # Sort by EV descending
    results.sort(key=lambda x: x[1], reverse=True)
    return results


def calculate_ev_fold(
    opponent_bet_size: float,
    pot_size: float = BASE_POT_SIZE
) -> float:
    """
    Calculate EV of folding when facing a bet.
    
    Args:
        opponent_bet_size: Opponent's bet size
        pot_size: Current pot size before opponent's bet
    
    Returns:
        EV of folding (typically 0, as we don't lose anything beyond what's already invested).
    """
    # When we fold, we don't invest more, so EV = 0
    # (We've already lost our blind if we're Big Blind, but that's sunk cost)
    return 0.0


def calculate_ev_call(
    hand: str,
    position: str,
    stack_sizes: Tuple[int, int],
    opponent_tendency: str,
    opponent_bet_size: float,
    pot_size: float = BASE_POT_SIZE
) -> float:
    """
    Calculate EV of calling opponent's bet.
    
    Convenience wrapper for calculate_ev with action="call".
    
    Args:
        hand: Starting hand notation
        position: Position
        stack_sizes: Tuple of (your_stack, opponent_stack)
        opponent_tendency: Opponent tendency
        opponent_bet_size: Opponent's bet size to call
        pot_size: Current pot size before opponent's bet
    
    Returns:
        Expected value of calling.
    """
    return calculate_ev(
        bet_size=opponent_bet_size,
        hand=hand,
        position=position,
        stack_sizes=stack_sizes,
        opponent_tendency=opponent_tendency,
        pot_size=pot_size,
        opponent_bet_size=opponent_bet_size,
        action="call"
    )
