"""
Bet size discretization for poker bet sizing search.
Defines the set of bet sizes to consider in the search space.
"""

from typing import List, Optional, Tuple


# Standard bet size increments (multiples of big blind)
STANDARD_BET_SIZES = [2.0, 2.5, 3.0, 3.5, 4.0, 5.0, 6.0, 7.0, 8.0, 10.0]

# Minimum bet size (2x big blind is standard opening raise)
MIN_BET_SIZE = 2.0

# Maximum reasonable bet size before going all-in (can be adjusted)
MAX_STANDARD_BET_SIZE = 10.0


def get_bet_sizes(
    stack_size: int,
    opponent_bet_size: Optional[float] = None,
    increment: float = 0.5,
    include_all_in: bool = True
) -> List[float]:
    """
    Generate list of bet sizes to consider in search.
    
    Args:
        stack_size: Your stack size in big blinds
        opponent_bet_size: Opponent's bet size if facing a bet (None for opening action)
        increment: Increment between bet sizes (default: 0.5 BB)
        include_all_in: Whether to include all-in as an option
    
    Returns:
        List of bet sizes in big blinds, sorted ascending.
        For opening: [2.0, 2.5, 3.0, ..., all_in]
        For facing bet: [call_size, raise_sizes..., all_in]
    """
    bet_sizes = []
    
    if opponent_bet_size is None:
        # Opening action: start from minimum bet size
        current = MIN_BET_SIZE
        while current <= min(stack_size, MAX_STANDARD_BET_SIZE):
            bet_sizes.append(current)
            current += increment
    else:
        # Facing a bet: include call option
        call_size = opponent_bet_size
        bet_sizes.append(call_size)
        
        # Minimum re-raise is typically 2x the opponent's bet
        min_raise = opponent_bet_size * 2.0
        current = min_raise
        
        # Generate raise sizes
        while current <= min(stack_size, MAX_STANDARD_BET_SIZE):
            if current > call_size:  # Must be larger than call
                bet_sizes.append(current)
            current += increment
    
    # Add all-in if requested and stack is larger than max standard bet
    if include_all_in and stack_size > MAX_STANDARD_BET_SIZE:
        bet_sizes.append(float(stack_size))
    
    # Remove duplicates and sort
    bet_sizes = sorted(list(set(bet_sizes)))
    
    return bet_sizes


def get_standard_bet_sizes(stack_size: int) -> List[float]:
    """
    Get standard bet sizes using predefined list, capped by stack size.
    
    Args:
        stack_size: Your stack size in big blinds
    
    Returns:
        List of bet sizes from STANDARD_BET_SIZES that are <= stack_size,
        plus all-in if stack_size > max standard bet.
    """
    bet_sizes = [bs for bs in STANDARD_BET_SIZES if bs <= stack_size]
    
    # Add all-in if stack is larger than max standard bet
    if stack_size > MAX_STANDARD_BET_SIZE:
        bet_sizes.append(float(stack_size))
    
    return bet_sizes


def get_bet_sizes_for_scenario(
    stack_size: int,
    opponent_bet_size: Optional[float] = None,
    use_standard: bool = True
) -> List[float]:
    """
    Get bet sizes for a specific scenario (opening or facing bet).
    
    Args:
        stack_size: Your stack size in big blinds
        opponent_bet_size: Opponent's bet size if facing a bet (None for opening)
        use_standard: If True, use STANDARD_BET_SIZES; if False, use incremental generation
    
    Returns:
        List of bet sizes to consider.
    """
    if use_standard:
        if opponent_bet_size is None:
            # Opening: use standard bet sizes
            return get_standard_bet_sizes(stack_size)
        else:
            # Facing bet: include call + standard raise sizes
            bet_sizes = [opponent_bet_size]  # Call option
            standard = get_standard_bet_sizes(stack_size)
            # Add raises that are > opponent's bet
            for bs in standard:
                if bs > opponent_bet_size:
                    bet_sizes.append(bs)
            return sorted(list(set(bet_sizes)))
    else:
        return get_bet_sizes(stack_size, opponent_bet_size)


def normalize_bet_size(bet_size: float, stack_size: int) -> float:
    """
    Normalize bet size to ensure it's valid (not negative, not exceeding stack).
    
    Args:
        bet_size: Proposed bet size in big blinds
        stack_size: Available stack size in big blinds
    
    Returns:
        Normalized bet size (capped at stack_size, minimum MIN_BET_SIZE for opening).
    """
    if bet_size < 0:
        return 0.0
    if bet_size > stack_size:
        return float(stack_size)
    return bet_size


def is_all_in(bet_size: float, stack_size: int, tolerance: float = 0.01) -> bool:
    """
    Check if a bet size represents going all-in.
    
    Args:
        bet_size: Bet size in big blinds
        stack_size: Stack size in big blinds
        tolerance: Tolerance for floating point comparison
    
    Returns:
        True if bet_size is approximately equal to stack_size.
    """
    return abs(bet_size - stack_size) < tolerance


def get_action_type(
    bet_size: float,
    opponent_bet_size: Optional[float],
    stack_size: int
) -> str:
    """
    Determine action type based on bet size and scenario.
    
    Args:
        bet_size: Proposed bet size
        opponent_bet_size: Opponent's bet size (None if opening)
        stack_size: Stack size
    
    Returns:
        "fold", "call", "raise", or "open"
    """
    if opponent_bet_size is None:
        # Opening action
        if bet_size == 0:
            return "fold"
        return "open"
    else:
        # Facing a bet
        if bet_size == 0:
            return "fold"
        if abs(bet_size - opponent_bet_size) < 0.01:
            return "call"
        if bet_size > opponent_bet_size:
            return "raise"
        return "fold"  # Invalid: bet_size < opponent_bet_size


def get_bet_size_description(bet_size: float, stack_size: int) -> str:
    """
    Get human-readable description of bet size.
    
    Args:
        bet_size: Bet size in big blinds
        stack_size: Stack size in big blinds
    
    Returns:
        Description string (e.g., "3x BB", "All-in (50 BB)")
    """
    if is_all_in(bet_size, stack_size):
        return f"All-in ({stack_size:.1f} BB)"
    return f"{bet_size:.1f}x BB"
