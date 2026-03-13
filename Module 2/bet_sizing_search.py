"""
Bet sizing search: Optimization and A*.
Uses A* and brute-force optimization to find optimal bet sizes that maximize expected value.
"""

from typing import Tuple, Optional, List, Dict, Any
from dataclasses import dataclass
from heapq import heappush, heappop
import logging
import sys
import importlib.util
from pathlib import Path

# Import dependencies (guard against duplicate path entries)
_module2_dir = str(Path(__file__).parent)
if _module2_dir not in sys.path:
    sys.path.insert(0, _module2_dir)
from ev_calculator import calculate_ev, calculate_ev_call, calculate_ev_fold
from bet_size_discretization import (
    get_bet_sizes_for_scenario, get_action_type, is_all_in
)
from heuristic import heuristic_hand_strength_based, get_heuristic

logger = logging.getLogger(__name__)

# Optional Module 1 integration: load propositional_logic_hand_decider if Module 1 exists
_propositional_logic_hand_decider: Optional[Any] = None
_module_1_path = Path(__file__).resolve().parent.parent / "Module 1" / "propositional_logic.py"
if _module_1_path.exists():
    try:
        _spec = importlib.util.spec_from_file_location("propositional_logic", _module_1_path)
        _mod = importlib.util.module_from_spec(_spec)
        if _spec and _spec.loader:
            _spec.loader.exec_module(_mod)
            _propositional_logic_hand_decider = getattr(_mod, "propositional_logic_hand_decider", None)
    except (ImportError, OSError, AttributeError) as exc:
        # If Module 1 cannot be loaded, we gracefully degrade by skipping
        # the optional playability filter instead of failing the entire module.
        logger.warning("Failed to load Module 1 for bet sizing search: %s", exc)


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
            "nodes_explored": 0,
        }
    
    # Get heuristic estimate once (h(n) is same for all nodes in this problem)
    h_score = get_heuristic(
        hand,
        position,
        stack_sizes,
        opponent_tendency,
        opponent_bet_size,
        pot_size,
        heuristic_type,
    )
    
    # Evaluate fold option
    fold_ev = calculate_ev_fold(opponent_bet_size or 0.0, pot_size) if opponent_bet_size else 0.0
    best_node = SearchNode(
        bet_size=0.0,
        ev=fold_ev,
        f_score=fold_ev + h_score,
        action="fold",
    )
    
    # Priority queue: nodes ordered by f_score (highest first for maximizing)
    open_set: List[SearchNode] = []
    
    # Add all bet sizes to open set with their f_scores
    for bet_size in bet_sizes:
        node = _create_search_node_for_bet_size(
            bet_size=bet_size,
            hand=hand,
            position=position,
            stack_sizes=stack_sizes,
            opponent_tendency=opponent_tendency,
            opponent_bet_size=opponent_bet_size,
            pot_size=pot_size,
            h_score=h_score,
        )
        if node is not None:
            heappush(open_set, node)
    
    # A* exploration: process nodes in order of f_score
    nodes_explored = 0
    
    while open_set:
        current = heappop(open_set)
        nodes_explored += 1
        
        # Update best if this node has higher actual EV
        if current.ev > best_node.ev:
            best_node = current
        
        # Early termination: if current node cannot beat the best EV even
        # under the optimistic heuristic, no remaining nodes can either.
        if _should_terminate_search(current, best_node):
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


def _create_search_node_for_bet_size(
    bet_size: float,
    hand: str,
    position: str,
    stack_sizes: Tuple[int, int],
    opponent_tendency: str,
    opponent_bet_size: Optional[float],
    pot_size: float,
    h_score: float,
) -> Optional[SearchNode]:
    """
    Create a SearchNode for a given bet size, or return None if the bet size
    corresponds to an invalid action in this scenario.
    """
    your_stack, _ = stack_sizes
    
    # Determine action type
    if opponent_bet_size is None:
        action = "open"
    else:
        action = get_action_type(bet_size, opponent_bet_size, your_stack)
        if action == "fold":
            return None  # Skip invalid or dominated sizes
    
    # Calculate actual EV (g(n))
    if action == "call":
        g_score = calculate_ev_call(
            hand,
            position,
            stack_sizes,
            opponent_tendency,
            opponent_bet_size,
            pot_size,
        )
    else:  # raise or open
        g_score = calculate_ev(
            bet_size,
            hand,
            position,
            stack_sizes,
            opponent_tendency,
            pot_size,
            opponent_bet_size,
            action,
        )
    
    # f(n) = g(n) + h(n)
    f_score = g_score + h_score
    
    return SearchNode(
        bet_size=bet_size,
        ev=g_score,
        f_score=f_score,
        action=action,
    )


def _should_terminate_search(current: SearchNode, best_node: SearchNode) -> bool:
    """
    Decide whether A* search can terminate early based on the heuristic bound.
    
    If the current node's f_score (g + h) is already below the best actual EV
    found so far, no future node can improve on best_node.ev, so we can stop.
    """
    return current.f_score < best_node.ev


def find_max_ev_bet_size(
    hand: str,
    position: str,
    stack_sizes: Tuple[int, int],
    opponent_tendency: str,
    opponent_bet_size: Optional[float] = None,
    pot_size: float = 1.5
) -> Dict:
    """
    Find optimal bet size by evaluating all bet sizes directly.
    
    This is a brute-force optimization that evaluates all possible bet sizes
    and returns the one with maximum EV. Does not use find_max_ev() function.
    
    Args:
        hand: Starting hand notation
        position: Position ("Button" or "Big Blind")
        stack_sizes: Tuple of (your_stack, opponent_stack) in big blinds
        opponent_tendency: Opponent tendency
        opponent_bet_size: Opponent's bet size if facing a bet (None for opening)
        pot_size: Current pot size
    
    Returns:
        Dictionary with:
        - "action": "fold", "call", or "raise"/"open"
        - "bet_size": optimal bet size (0.0 for fold)
        - "ev": expected value of optimal action
        - "search_method": "brute_force"
        - "nodes_explored": number of bet sizes evaluated
    """
    your_stack, _ = stack_sizes
    
    # Get all possible bet sizes
    bet_sizes = get_bet_sizes_for_scenario(your_stack, opponent_bet_size)
    
    # Evaluate fold option
    fold_ev = calculate_ev_fold(opponent_bet_size or 0.0, pot_size) if opponent_bet_size else 0.0
    
    best_bet_size = 0.0
    best_ev = fold_ev
    best_action = "fold"
    nodes_explored = 1  # Fold option
    
    # Evaluate all bet sizes and find the one with maximum EV
    for bet_size in bet_sizes:
        nodes_explored += 1
        
        # Determine action type
        if opponent_bet_size is None:
            action = "open"
        else:
            action = get_action_type(bet_size, opponent_bet_size, your_stack)
            if action == "fold":
                continue  # Skip invalid
        
        # Calculate EV
        if action == "call":
            ev = calculate_ev_call(
                hand, position, stack_sizes, opponent_tendency,
                opponent_bet_size, pot_size
            )
        else:  # raise or open
            ev = calculate_ev(
                bet_size, hand, position, stack_sizes, opponent_tendency,
                pot_size, opponent_bet_size, action
            )
        
        # Update best if this has higher EV
        if ev > best_ev:
            best_ev = ev
            best_bet_size = bet_size
            best_action = action
    
    return {
        "action": best_action,
        "bet_size": best_bet_size,
        "ev": best_ev,
        "search_method": "brute_force",
        "nodes_explored": nodes_explored
    }


def optimal_bet_sizing_search(
    hand: str,
    position: str,
    stack_sizes: Tuple[int, int],
    opponent_tendency: str,
    search_algorithm: str = "a_star",
    use_module1: bool = True,
    module1_result: Optional[Dict] = None,
    opponent_bet_size: Optional[float] = None,
    pot_size: float = 1.5,
    heuristic_type: str = "hand_strength",
) -> Dict:
    """
    Unified entry point: optimal bet size using Module 1 (optional) and A* or brute-force optimization.

    Module 1 integration in two ways:
    1. Pass in pre-computed Module 1 output (knowledge base / playability): if module1_result
       is provided, it is used to filter (fold if not playable) and Module 1 is not called again.
    2. If module1_result is not provided and use_module1 is True, Module 1 is called internally
       to get playability; if not playable, returns fold without searching.

    Args:
        hand: Starting hand notation (e.g. "AA", "KAs").
        position: "Button" or "Big Blind".
        stack_sizes: (your_stack, opponent_stack) in big blinds.
        opponent_tendency: "Tight", "Loose", "Aggressive", "Passive", or "Unknown".
        search_algorithm: "a_star" or "brute_force".
        use_module1: If True and module1_result not provided, call Module 1 to filter by playability.
        module1_result: Optional pre-computed Module 1 output (playable, reason, knowledge_base, ...).
            When provided, used instead of calling Module 1; non-playable hands return fold.
        opponent_bet_size: Opponent's bet if facing a bet (None for opening).
        pot_size: Current pot size in big blinds.
        heuristic_type: Heuristic for A* ("hand_strength" or other).

    Returns:
        Dict with: action, bet_size, expected_value, reason, search_algorithm, module1_result.
        module1_result is the Module 1 output when used or passed in, else {}.
    """
    your_stack, _ = stack_sizes
    m1_result: Dict = {}

    # Use passed-in Module 1 result (knowledge base / playability from Module 1) if provided
    if module1_result is not None:
        m1_result = module1_result
        if not module1_result.get("playable", False):
            return {
                "action": "fold",
                "bet_size": 0.0,
                "expected_value": 0.0,
                "reason": module1_result.get("reason", "Hand not playable (Module 1)."),
                "search_algorithm": "module1_filter",
                "module1_result": m1_result,
            }
    # Otherwise optionally call Module 1
    elif use_module1 and _propositional_logic_hand_decider is not None:
        m1 = _propositional_logic_hand_decider(
            hand, position, your_stack, opponent_tendency,
            opponent_bet_size=opponent_bet_size,
        )
        m1_result = m1
        if not m1.get("playable", False):
            return {
                "action": "fold",
                "bet_size": 0.0,
                "expected_value": 0.0,
                "reason": m1.get("reason", "Hand not playable (Module 1)."),
                "search_algorithm": "module1_filter",
                "module1_result": m1_result,
            }

    if search_algorithm == "brute_force":
        raw = find_max_ev_bet_size(
            hand, position, stack_sizes, opponent_tendency,
            opponent_bet_size=opponent_bet_size,
            pot_size=pot_size,
        )
    else:
        raw = a_star_search(
            hand, position, stack_sizes, opponent_tendency,
            opponent_bet_size=opponent_bet_size,
            pot_size=pot_size,
            heuristic_type=heuristic_type,
        )

    action = raw["action"]
    bet_size = raw["bet_size"]
    ev = raw["ev"]
    method = raw["search_method"]
    if action == "fold":
        reason = f"Fold has highest EV ({ev:.2f} BB) in this scenario."
    elif action == "call":
        reason = f"Call {opponent_bet_size or 0:.1f}x BB with EV {ev:.2f} BB."
    elif action == "open":
        reason = f"Open {bet_size:.1f}x BB with EV {ev:.2f} BB ({method})."
    else:
        reason = f"Raise to {bet_size:.1f}x BB with EV {ev:.2f} BB ({method})."

    return {
        "action": action,
        "bet_size": bet_size,
        "expected_value": ev,
        "reason": reason,
        "search_algorithm": method,
        "module1_result": m1_result,
    }
