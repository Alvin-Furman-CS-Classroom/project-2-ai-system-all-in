"""
Bet sizing search algorithms: A*, IDA*, and Beam Search.
Uses informed search to find optimal bet sizes that maximize expected value.
"""

from typing import Tuple, Optional, List, Dict, Set
from dataclasses import dataclass
from heapq import heappush, heappop
import sys
from pathlib import Path

# Import dependencies
sys.path.insert(0, str(Path(__file__).parent))
from ev_calculator import calculate_ev, calculate_ev_call, calculate_ev_fold
from bet_size_discretization import (
    get_bet_sizes_for_scenario, get_action_type, is_all_in
)
from heuristic import heuristic_hand_strength_based, get_heuristic


@dataclass
class SearchNode:
    """Node in the search space representing a bet size."""
    bet_size: float
    ev: float  # Actual EV of this bet size (g(n))
    f_score: float  # f(n) = g(n) + h(n) for A*
    action: str  # "fold", "call", "raise", or "open"
    parent: Optional['SearchNode'] = None
    
    def __lt__(self, other):
        """For priority queue: lower f_score = higher priority (we're maximizing EV)."""
        # For maximizing EV, we want higher f_score first, so invert comparison
        return self.f_score > other.f_score


def a_star_search(
    hand: str,
    position: str,
    stack_sizes: Tuple[int, int],
    opponent_tendency: str,
    opponent_bet_size: Optional[float] = None,
    pot_size: float = 1.5,
    heuristic_type: str = "hand_strength"
) -> Dict:
    """
    A* search algorithm to find optimal bet size.
    
    A* uses f(n) = g(n) + h(n) where:
    - g(n) = actual EV of current bet size
    - h(n) = heuristic estimate of maximum achievable EV
    - f(n) = total estimated value (used to prioritize exploration)
    
    For bet sizing, we evaluate bet sizes in order of f_score,
    prioritizing those with highest estimated total value.
    
    Args:
        hand: Starting hand notation
        position: Position ("Button" or "Big Blind")
        stack_sizes: Tuple of (your_stack, opponent_stack) in big blinds
        opponent_tendency: Opponent tendency
        opponent_bet_size: Opponent's bet size if facing a bet (None for opening)
        pot_size: Current pot size
        heuristic_type: Type of heuristic to use
    
    Returns:
        Dictionary with:
        - "action": "fold", "call", or "raise"/"open"
        - "bet_size": optimal bet size (0.0 for fold)
        - "ev": expected value of optimal action
        - "search_method": "a_star"
        - "nodes_explored": number of nodes explored
    """
    your_stack, _ = stack_sizes
    
    # Get all possible bet sizes (search space)
    bet_sizes = get_bet_sizes_for_scenario(your_stack, opponent_bet_size)
    
    if not bet_sizes:
        return {
            "action": "fold",
            "bet_size": 0.0,
            "ev": 0.0,
            "search_method": "a_star",
            "nodes_explored": 0
        }
    
    # Get heuristic estimate once (h(n) is same for all nodes in this problem)
    h_score = get_heuristic(
        hand, position, stack_sizes, opponent_tendency,
        opponent_bet_size, pot_size, heuristic_type
    )
    
    # Evaluate fold option
    fold_ev = calculate_ev_fold(opponent_bet_size or 0.0, pot_size) if opponent_bet_size else 0.0
    best_node = SearchNode(
        bet_size=0.0,
        ev=fold_ev,
        f_score=fold_ev + h_score,
        action="fold"
    )
    
    # Priority queue: nodes ordered by f_score (highest first for maximizing)
    open_set = []
    
    # Add all bet sizes to open set with their f_scores
    for bet_size in bet_sizes:
        # Determine action type
        if opponent_bet_size is None:
            action = "open"
        else:
            action = get_action_type(bet_size, opponent_bet_size, your_stack)
            if action == "fold":
                continue  # Skip invalid
        
        # Calculate actual EV (g(n))
        if action == "call":
            g_score = calculate_ev_call(
                hand, position, stack_sizes, opponent_tendency,
                opponent_bet_size, pot_size
            )
        else:  # raise or open
            g_score = calculate_ev(
                bet_size, hand, position, stack_sizes, opponent_tendency,
                pot_size, opponent_bet_size, action
            )
        
        # f(n) = g(n) + h(n)
        f_score = g_score + h_score
        
        node = SearchNode(
            bet_size=bet_size,
            ev=g_score,
            f_score=f_score,
            action=action
        )
        
        heappush(open_set, node)
    
    # A* exploration: process nodes in order of f_score
    nodes_explored = 0
    
    while open_set:
        current = heappop(open_set)
        nodes_explored += 1
        
        # Update best if this node has higher actual EV
        if current.ev > best_node.ev:
            best_node = current
        
        # Early termination: if current f_score < best EV, no better solutions exist
        # (since f_score = g(n) + h(n) and h(n) estimates max, if f < best_g, then
        # all remaining nodes have g(n) + h(n) < best_g, so g(n) < best_g)
        if current.f_score < best_node.ev:
            break
    
    # Determine final action
    if best_node.bet_size == 0.0:
        final_action = "fold"
    elif opponent_bet_size and abs(best_node.bet_size - opponent_bet_size) < 0.01:
        final_action = "call"
    elif opponent_bet_size and best_node.bet_size > opponent_bet_size:
        final_action = "raise"
    else:
        final_action = "open"
    
    return {
        "action": final_action,
        "bet_size": best_node.bet_size,
        "ev": best_node.ev,
        "search_method": "a_star",
        "nodes_explored": nodes_explored
    }
