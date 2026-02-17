"""
Heuristic functions for bet sizing search algorithms.
Provides estimates of maximum expected value to guide A* and other informed search algorithms.

Heuristics vs Optimization:
- Heuristics: Fast estimates used to guide search (heuristic_hand_strength_based, heuristic_optimistic_simple)
- Optimization: Exact solution by evaluating all options (find_max_ev) - use for comparison/testing, not in search
"""

from typing import Tuple, Optional
import sys
from pathlib import Path

# Import from same module
sys.path.insert(0, str(Path(__file__).parent))
from ev_calculator import calculate_ev, get_hand_equity
from bet_size_discretization import get_bet_sizes_for_scenario, is_all_in


def find_max_ev(
    hand: str,
    position: str,
    stack_sizes: Tuple[int, int],
    opponent_tendency: str,
    opponent_bet_size: Optional[float] = None,
    pot_size: float = 1.5
) -> float:
    """
    Optimization function: Find maximum EV by evaluating all bet sizes.
    
    NOTE: This is NOT a heuristic - it solves the optimization problem directly
    by evaluating all possible bet sizes. Use this for:
    - Finding the true optimal solution (for comparison/testing)
    - As a baseline to compare search algorithm results
    
    For use in search algorithms, use actual heuristics like:
    - heuristic_hand_strength_based() (fast, informative)
    - heuristic_optimistic_simple() (very fast, less accurate)
    
    Args:
        hand: Starting hand notation
        position: Position ("Button" or "Big Blind")
        stack_sizes: Tuple of (your_stack, opponent_stack) in big blinds
        opponent_tendency: Opponent tendency
        opponent_bet_size: Opponent's bet size if facing a bet (None for opening)
        pot_size: Current pot size
    
    Returns:
        Maximum EV found among all bet sizes.
    """
    your_stack, _ = stack_sizes
    
    # Get all possible bet sizes for this scenario
    bet_sizes = get_bet_sizes_for_scenario(your_stack, opponent_bet_size)
    
    if not bet_sizes:
        return 0.0
    
    # Calculate EV for each bet size and take maximum
    max_ev = float('-inf')
    for bet_size in bet_sizes:
        if opponent_bet_size is None:
            # Opening action
            action = "open"
        else:
            # Determine action type
            if abs(bet_size - opponent_bet_size) < 0.01:
                action = "call"
            elif bet_size > opponent_bet_size:
                action = "raise"
            else:
                continue  # Skip invalid bet sizes
        
        ev = calculate_ev(
            bet_size=bet_size,
            hand=hand,
            position=position,
            stack_sizes=stack_sizes,
            opponent_tendency=opponent_tendency,
            pot_size=pot_size,
            opponent_bet_size=opponent_bet_size,
            action=action
        )
        max_ev = max(max_ev, ev)
    
    return max_ev if max_ev != float('-inf') else 0.0


def heuristic_hand_strength_based(
    hand: str,
    position: str,
    stack_sizes: Tuple[int, int],
    opponent_tendency: str,
    opponent_bet_size: Optional[float] = None,
    pot_size: float = 1.5
) -> float:
    """
    Heuristic: Estimate EV based on hand strength and position.
    
    NOTE: This heuristic may not be perfectly admissible (can overestimate in some cases).
    For guaranteed admissibility, use heuristic_optimistic_simple() with additional
    conservative adjustments, or use find_max_ev() for exact solutions.
    
    Faster but less accurate than evaluating all bet sizes.
    Uses hand equity and position advantage as proxies.
    
    Args:
        hand: Starting hand notation
        position: Position ("Button" or "Big Blind")
        stack_sizes: Tuple of (your_stack, opponent_stack) in big blinds
        opponent_tendency: Opponent tendency
        opponent_bet_size: Opponent's bet size if facing a bet (None for opening)
        pot_size: Current pot size
    
    Returns:
        Estimated EV based on hand strength.
        WARNING: May overestimate in some cases (not perfectly admissible).
    """
    equity = get_hand_equity(hand)
    your_stack, opponent_stack = stack_sizes
    
    # Base EV estimate: equity × pot - investment
    # Use conservative estimates
    if opponent_bet_size is None:
        # Opening: estimate with moderate bet size (3x BB)
        estimated_bet = min(3.0, your_stack)
        base_ev = equity * (pot_size + estimated_bet * 2) - estimated_bet
    else:
        # Facing bet: estimate with call
        base_ev = equity * (pot_size + opponent_bet_size * 2) - opponent_bet_size
    
    # Position advantage: Button has advantage (small multiplier)
    position_multiplier = 1.05 if position.lower() in ("button", "btn") else 1.0
    
    # Opponent tendency adjustments
    tendency_adjustment = {
        "Tight": 1.0,      # Neutral
        "Loose": 0.95,     # Slightly reduce
        "Aggressive": 0.7, # Reduce significantly (they raise frequently)
        "Passive": 1.0,    # Neutral
        "Unknown": 0.95    # Slightly conservative
    }
    adjustment = tendency_adjustment.get(opponent_tendency.strip(), 0.95)
    
    estimated_ev = base_ev * position_multiplier * adjustment
    
    # Ensure non-negative
    return max(0.0, estimated_ev)


def heuristic_optimistic_simple(
    hand: str,
    position: str,
    stack_sizes: Tuple[int, int],
    opponent_tendency: str,
    opponent_bet_size: Optional[float] = None,
    pot_size: float = 1.5
) -> float:
    """
    Simple optimistic heuristic: assumes we win the pot with our hand equity.
    
    NOTE: This heuristic is NOT admissible - it can overestimate true maximum EV.
    It's fast but may cause A* to miss optimal solutions in some cases.
    
    Very fast but less informative. Good for initial exploration or when
    perfect optimality is not required.
    
    Args:
        hand: Starting hand notation
        position: Position
        stack_sizes: Tuple of (your_stack, opponent_stack)
        opponent_tendency: Opponent tendency
        opponent_bet_size: Opponent's bet size if facing a bet
        pot_size: Current pot size
    
    Returns:
        Optimistic EV estimate (equity × pot).
        WARNING: May overestimate - not admissible for A* optimality guarantee.
    """
    equity = get_hand_equity(hand)
    
    if opponent_bet_size is None:
        # Opening: optimistic = equity × (pot + reasonable bet)
        return equity * (pot_size + 3.0)
    else:
        # Facing bet: optimistic = equity × (pot + opponent bet) - call cost
        return equity * (pot_size + opponent_bet_size) - opponent_bet_size


def get_heuristic(
    hand: str,
    position: str,
    stack_sizes: Tuple[int, int],
    opponent_tendency: str,
    opponent_bet_size: Optional[float] = None,
    pot_size: float = 1.5,
    heuristic_type: str = "hand_strength"
) -> float:
    """
    Get heuristic value using specified heuristic type.
    
    Args:
        hand: Starting hand notation
        position: Position
        stack_sizes: Tuple of (your_stack, opponent_stack)
        opponent_tendency: Opponent tendency
        opponent_bet_size: Opponent's bet size if facing a bet
        pot_size: Current pot size
        heuristic_type: Type of heuristic to use
            - "hand_strength": Based on hand equity and position (balanced, recommended)
            - "optimistic": Simple optimistic estimate (fastest, less accurate)
    
    Returns:
        Heuristic value (estimated maximum EV).
    
    Note:
        For finding the true optimal solution, use find_max_ev() instead.
        Heuristics are fast estimates for guiding search, not exact solutions.
    """
    if heuristic_type == "hand_strength":
        return heuristic_hand_strength_based(
            hand, position, stack_sizes, opponent_tendency,
            opponent_bet_size, pot_size
        )
    elif heuristic_type == "optimistic":
        return heuristic_optimistic_simple(
            hand, position, stack_sizes, opponent_tendency,
            opponent_bet_size, pot_size
        )
    else:
        raise ValueError(
            f"Unknown heuristic type: {heuristic_type}. "
            f"Use 'hand_strength' or 'optimistic'. "
            f"For optimization (not heuristic), use find_max_ev()."
        )


def heuristic_for_state(
    current_bet_size: float,
    hand: str,
    position: str,
    stack_sizes: Tuple[int, int],
    opponent_tendency: str,
    opponent_bet_size: Optional[float] = None,
    pot_size: float = 1.5,
    heuristic_type: str = "hand_strength"
) -> float:
    """
    Get heuristic value for a specific search state.
    
    This estimates the remaining value from the current state to the goal.
    For A*, this is h(n) = estimated cost from n to goal.
    
    Args:
        current_bet_size: Current bet size being considered
        hand: Starting hand notation
        position: Position
        stack_sizes: Tuple of (your_stack, opponent_stack)
        opponent_tendency: Opponent tendency
        opponent_bet_size: Opponent's bet size if facing a bet
        pot_size: Current pot size
        heuristic_type: Type of heuristic to use
    
    Returns:
        Heuristic value (estimated remaining EV from this state).
    """
    # For bet sizing, the heuristic estimates maximum EV achievable
    # We can use the same heuristic regardless of current bet size
    # (since we're searching for the optimal bet size)
    return get_heuristic(
        hand, position, stack_sizes, opponent_tendency,
        opponent_bet_size, pot_size, heuristic_type
    )
