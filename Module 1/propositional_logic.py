"""
Rule-based hand playability using propositional logic.
Rules combine hand strength, position, stack size, and opponent tendency.
Implements knowledge base with CNF-encoded rules and inference methods.
"""

from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass

# Ordered list of 169 hands (rank 1 = best), matching POKER_HAND_WIN_PERCENTAGES.md.
HAND_RANK_LIST = [
    "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "KAs", "QAs", "JAs", "KAo", "QAo", "TAs", "66", "JAo", "QKs", "9As", "TAo", "JKs", "8As", "TKs", "5As", "QKo", "9Ao", "JKo", "7As", "TKo", "JQs", "6As",
    "8Ao", "4As", "55", "9Ks", "3As", "6Ao", "8Ks", "TQs", "JQo", "2As", "9Ko", "9Qs", "TJs", "7Ks", "5Ao", "4Ao", "7Ao", "6Ks", "44", "TQo", "7Ko", "3Ao", "9Qo", "8Qs", "8Ko", "9Js", "TJo", "5Ks", "2Ao", "6Ko",
    "4Ks", "33", "8Js", "7Qs", "9Jo", "5Ko", "3Ks", "8Qo", "9Ts", "5Qs", "2Ks", "6Qs", "9To", "7Js", "3Ko", "3Qs", "4Qs", "8Ts", "4Ko", "8Jo", "6Qo", "6Js", "2Qs", "7Qo", "89s", "22", "2Ko", "7Ts",
    "5Js", "8To", "4Js", "5Qo", "7Jo", "4Qo", "79s", "6Ts", "3Qo", "7To", "3Js", "6Jo", "89o", "5Jo", "2Js", "69s", "5Ts", "2Qo", "78s", "68s", "79o", "4Ts", "6To", "4Jo", "3Jo", "59s", "67s", "3Ts",
    "2Ts", "2Jo", "78o", "58s", "5To", "69o", "49s", "57s", "39s", "4To", "48s", "29s", "56s", "3To", "68o", "59o", "67o", "47s", "45s", "58o", "2To", "49o", "38s", "57o", "39o", "46s", "35s", "28s", "37s", "29o", "56o", "34s", "36s", "48o", "47o", "45o", "46o", "27s", "25s", "26s", "24s", "37o", "28o", "38o", "36o", "35o", "34o", "23s", "27o", "25o", "26o", "24o", "23o",
]

# Hand strength tier thresholds (rank 1 = best)
HAND_STRENGTH_PREMIUM_MAX = 30
HAND_STRENGTH_STRONG_MAX = 60
HAND_STRENGTH_PLAYABLE_MAX = 87
HAND_STRENGTH_MARGINAL_MAX = 116

# Stack size thresholds (in big blinds)
STACK_SIZE_ULTRA_SHORT_MAX = 10
STACK_SIZE_SHORT_MAX = 20


@dataclass
class CNFRule:
    """Represents a propositional logic rule in CNF (Conjunctive Normal Form)."""
    name: str
    cnf: str  # CNF formula as string
    clauses: List[List[str]]  # List of clauses, each clause is list of literals
    description: str


class KnowledgeBase:
    """Knowledge base for propositional logic rules in CNF format."""
    
    def __init__(self):
        self.rules: List[CNFRule] = []
        self.facts: Dict[str, bool] = {}
        self.inference_chain: List[str] = []
    
    def add_rule(self, rule: CNFRule):
        """Add a rule to the knowledge base."""
        self.rules.append(rule)
    
    def add_fact(self, fact: str, value: bool):
        """Add a fact to the knowledge base."""
        self.facts[fact] = value
    
    def get_fact(self, fact: str) -> Optional[bool]:
        """Get the value of a fact, or None if unknown."""
        return self.facts.get(fact)
    
    def query(self, goal: str) -> Tuple[bool, List[str]]:
        """
        Query the knowledge base for a goal using backward chaining.
        Returns (result, inference_chain).
        """
        return self._backward_chain(goal, set())
    
    def _backward_chain(self, goal: str, visited: Set[str]) -> Tuple[bool, List[str]]:
        """Backward chaining: work backwards from goal to facts."""
        if goal in self.facts:
            return self.facts[goal], [f"Goal '{goal}' is a known fact: {self.facts[goal]}"]
        
        if goal in visited:
            return False, [f"Circular dependency detected for '{goal}'"]
        
        visited.add(goal)
        chain = [f"Attempting to prove '{goal}'"]
        
        # Find rules that can derive this goal
        for rule in self.rules:
            if goal in self._get_conclusions(rule):
                # For CNF rules, we need to check if we can conclude the goal
                # A clause like (¬A ∨ ¬B ∨ C) means IF (A ∧ B) THEN C
                # To conclude C, we need A=True AND B=True
                premises_satisfied = True
                premise_chain = []
                
                for clause in rule.clauses:
                    if goal not in clause:
                        continue  # Skip clauses that don't contain the goal
                    
                    # Check if all premises (non-goal literals) are satisfied
                    # For (¬A ∨ ¬B ∨ C), to conclude C, we need A=True and B=True
                    all_premises_satisfied = True
                    clause_premise_chain = []
                    
                    for literal in clause:
                        if literal == goal:
                            continue  # Skip the conclusion itself
                        
                        premise_satisfied = False
                        if literal.startswith("¬"):
                            # Negated premise like ¬A in (¬A ∨ ¬B ∨ C)
                            # To conclude C, we need A to be True (so ¬A is False, forcing C)
                            fact = literal[1:]
                            if fact in self.facts:
                                if self.facts[fact]:  # Fact is True, so negation is False
                                    premise_satisfied = True
                                    clause_premise_chain.append(f"Fact '{fact}' is True → '{literal}' is False (forces conclusion)")
                            else:
                                # Try to prove the fact
                                result, sub_chain = self._backward_chain(fact, visited.copy())
                                if result:  # Fact is True, so negation is False
                                    premise_satisfied = True
                                    clause_premise_chain.extend(sub_chain)
                        else:
                            # Positive premise: fact must be True
                            if literal in self.facts:
                                if self.facts[literal]:
                                    premise_satisfied = True
                                    clause_premise_chain.append(f"Fact '{literal}' is True")
                            else:
                                # Try to prove the fact
                                result, sub_chain = self._backward_chain(literal, visited.copy())
                                if result:
                                    premise_satisfied = True
                                    clause_premise_chain.extend(sub_chain)
                        
                        if not premise_satisfied:
                            all_premises_satisfied = False
                            break
                    
                    if all_premises_satisfied:
                        # This clause allows us to conclude the goal
                        premise_chain.extend(clause_premise_chain)
                        premises_satisfied = True
                        break
                    else:
                        premises_satisfied = False
                
                if premises_satisfied:
                    self.facts[goal] = True
                    chain.extend(premise_chain)
                    chain.append(f"Proved '{goal}' using {rule.name}")
                    return True, chain
        
        return False, chain + [f"Cannot prove '{goal}'"]
    
    def _get_conclusions(self, rule: CNFRule) -> List[str]:
        """Extract all conclusions from a rule."""
        conclusions = []
        valid_conclusions = ["playable", "stack_ok", "can_proceed", "final_playable"]
        for clause in rule.clauses:
            for literal in clause:
                if not literal.startswith("¬") and literal in valid_conclusions:
                    if literal not in conclusions:
                        conclusions.append(literal)
        return conclusions
    
    def to_dict(self) -> Dict:
        """Convert knowledge base to dictionary for output."""
        return {
            "rules": [
                {
                    "name": rule.name,
                    "cnf": rule.cnf,
                    "description": rule.description
                }
                for rule in self.rules
            ],
            "facts": self.facts.copy(),
            "inference_chain": self.inference_chain.copy()
        }


def _rank_to_tier(rank: int) -> str:
    """Rank 1-169 -> tier name."""
    if rank <= HAND_STRENGTH_PREMIUM_MAX:
        return "Premium"
    if rank <= HAND_STRENGTH_STRONG_MAX:
        return "Strong"
    if rank <= HAND_STRENGTH_PLAYABLE_MAX:
        return "Playable"
    if rank <= HAND_STRENGTH_MARGINAL_MAX:
        return "Marginal"
    return "Weak"


def _normalize_hand(hand: str) -> Optional[str]:
    """Return standard hand notation (as in HAND_RANK_LIST) or None if unknown."""
    h = hand.strip()
    if h in HAND_RANK_LIST:
        return h
    # Map common input "AKs"/"AKo" to list form "KAs"/"KAo" (document uses high card first)
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
    # Try two-char + s/o (list uses high rank first: KAs not AKs)
    if len(h) >= 2:
        two = (h[0] + h[1]).upper()
        rest = h[2:].strip().lower()
        # Check if exact match exists
        if two + "s" in HAND_RANK_LIST and rest in ("s", "suit", "suited", ""):
            return two + "s"
        if two + "o" in HAND_RANK_LIST and rest in ("o", "off", "offsuit", ""):
            return two + "o"
        if two in HAND_RANK_LIST and (rest == "" or "pair" in rest):
            return two
        # Try reversed (for cases like "AKs" -> "KAs")
        if len(two) == 2:
            reversed_two = two[1] + two[0]
            if reversed_two + "s" in HAND_RANK_LIST and rest in ("s", "suit", "suited", ""):
                return reversed_two + "s"
            if reversed_two + "o" in HAND_RANK_LIST and rest in ("o", "off", "offsuit", ""):
                return reversed_two + "o"
    return None


def _get_hand_rank(hand: str) -> Optional[int]:
    """Return 1-based rank (1 = best) or None if unknown."""
    norm = _normalize_hand(hand)
    if norm is None:
        return None
    try:
        return HAND_RANK_LIST.index(norm) + 1
    except ValueError:
        return None


def _create_cnf_rules() -> List[CNFRule]:
    """
    Create knowledge base with CNF-encoded propositional logic rules.
    CNF format: (A ∨ B) ∧ (C ∨ D) where each clause is a disjunction.
    For implication A → B, CNF is (¬A ∨ B).
    """
    rules = []
    
    # Rule 1: Position must be valid
    # IF position_valid THEN can_proceed
    # CNF: (¬position_valid ∨ can_proceed)
    rules.append(CNFRule(
        name="Rule 1: Valid Position",
        cnf="(¬position_valid ∨ can_proceed)",
        clauses=[["¬position_valid", "can_proceed"]],
        description="Position must be Button or Big Blind to proceed"
    ))
    
    # Rule 2: Hand strength for Button vs Aggressive/Loose
    # IF (position_Button ∧ hand_strength_strong_or_better ∧ opponent_Aggressive_or_Loose) THEN playable
    # CNF: (¬position_Button ∨ ¬hand_strength_strong ∨ ¬opponent_Aggressive_Loose ∨ playable)
    rules.append(CNFRule(
        name="Rule 2: Button vs Aggressive/Loose",
        cnf="(¬position_Button ∨ ¬hand_strength_strong ∨ ¬opponent_Aggressive_Loose ∨ playable)",
        clauses=[["¬position_Button", "¬hand_strength_strong", "¬opponent_Aggressive_Loose", "playable"]],
        description="Button with Strong+ hands vs Aggressive/Loose opponent → playable"
    ))
    
    # Rule 3: Hand strength for Button vs Tight
    # IF (position_Button ∧ hand_strength_marginal_or_better ∧ opponent_Tight) THEN playable
    # CNF: (¬position_Button ∨ ¬hand_strength_marginal ∨ ¬opponent_Tight ∨ playable)
    rules.append(CNFRule(
        name="Rule 3: Button vs Tight",
        cnf="(¬position_Button ∨ ¬hand_strength_marginal ∨ ¬opponent_Tight ∨ playable)",
        clauses=[["¬position_Button", "¬hand_strength_marginal", "¬opponent_Tight", "playable"]],
        description="Button with Marginal+ hands vs Tight opponent → playable"
    ))
    
    # Rule 4: Hand strength for Button vs Passive
    # IF (position_Button ∧ hand_strength_playable_or_better ∧ opponent_Passive) THEN playable
    # CNF: (¬position_Button ∨ ¬hand_strength_playable ∨ ¬opponent_Passive ∨ playable)
    rules.append(CNFRule(
        name="Rule 4: Button vs Passive",
        cnf="(¬position_Button ∨ ¬hand_strength_playable ∨ ¬opponent_Passive ∨ playable)",
        clauses=[["¬position_Button", "¬hand_strength_playable", "¬opponent_Passive", "playable"]],
        description="Button with Playable+ hands vs Passive opponent → playable"
    ))
    
    # Rule 5: Hand strength for Button vs Unknown
    # IF (position_Button ∧ hand_strength_playable_or_better ∧ opponent_Unknown) THEN playable
    # CNF: (¬position_Button ∨ ¬hand_strength_playable ∨ ¬opponent_Unknown ∨ playable)
    rules.append(CNFRule(
        name="Rule 5: Button vs Unknown",
        cnf="(¬position_Button ∨ ¬hand_strength_playable ∨ ¬opponent_Unknown ∨ playable)",
        clauses=[["¬position_Button", "¬hand_strength_playable", "¬opponent_Unknown", "playable"]],
        description="Button with Playable+ hands vs Unknown opponent → playable"
    ))
    
    # Rule 6: Hand strength for Big Blind vs Unknown
    # IF (position_Big_Blind ∧ hand_strength_strong_or_better ∧ opponent_Unknown) THEN playable
    # CNF: (¬position_Big_Blind ∨ ¬hand_strength_strong ∨ ¬opponent_Unknown ∨ playable)
    rules.append(CNFRule(
        name="Rule 6: Big Blind vs Unknown",
        cnf="(¬position_Big_Blind ∨ ¬hand_strength_strong ∨ ¬opponent_Unknown ∨ playable)",
        clauses=[["¬position_Big_Blind", "¬hand_strength_strong", "¬opponent_Unknown", "playable"]],
        description="Big Blind with Strong+ hands vs Unknown opponent → playable"
    ))
    
    # Rule 7: Stack size for ultra-short stack
    # IF (stack_size_ultra_short ∧ hand_strength_premium) THEN stack_ok
    # CNF: (¬stack_size_ultra_short ∨ ¬hand_strength_premium ∨ stack_ok)
    rules.append(CNFRule(
        name="Rule 7: Ultra-Short Stack Premium",
        cnf="(¬stack_size_ultra_short ∨ ¬hand_strength_premium ∨ stack_ok)",
        clauses=[["¬stack_size_ultra_short", "¬hand_strength_premium", "stack_ok"]],
        description="Ultra-short stack (<10 BB) requires Premium hands → stack_ok"
    ))
    
    # Rule 8: Stack size for short stack
    # IF (stack_size_short ∧ hand_strength_strong_or_better) THEN stack_ok
    # CNF: (¬stack_size_short ∨ ¬hand_strength_strong ∨ stack_ok)
    rules.append(CNFRule(
        name="Rule 8: Short Stack Strong",
        cnf="(¬stack_size_short ∨ ¬hand_strength_strong ∨ stack_ok)",
        clauses=[["¬stack_size_short", "¬hand_strength_strong", "stack_ok"]],
        description="Short stack (10-20 BB) requires Strong+ hands → stack_ok"
    ))
    
    # Rule 9: Adequate stack allows all hands
    # IF stack_size_adequate THEN stack_ok
    # CNF: (¬stack_size_adequate ∨ stack_ok)
    rules.append(CNFRule(
        name="Rule 9: Adequate Stack",
        cnf="(¬stack_size_adequate ∨ stack_ok)",
        clauses=[["¬stack_size_adequate", "stack_ok"]],
        description="Adequate stack (≥20 BB) allows all hands → stack_ok"
    ))
    
    # Rule 10: Final playability
    # IF (can_proceed ∧ stack_ok ∧ playable) THEN final_playable
    # CNF: (¬can_proceed ∨ ¬stack_ok ∨ ¬playable ∨ final_playable)
    rules.append(CNFRule(
        name="Rule 10: Final Decision",
        cnf="(¬can_proceed ∨ ¬stack_ok ∨ ¬playable ∨ final_playable)",
        clauses=[["¬can_proceed", "¬stack_ok", "¬playable", "final_playable"]],
        description="All conditions met → hand is playable"
    ))
    
    return rules


def _derive_facts_from_input(
    hand: str,
    position: str,
    stack_size: int,
    opponent_tendency: str,
    kb: KnowledgeBase,
    opponent_bet_size: Optional[float] = None,
) -> Tuple[Optional[int], Optional[str], List[str]]:
    """
    Derive facts from input and add to knowledge base.

    Returns:
        (hand_rank, hand_tier, facts_added)

    Enhancement: opponent_bet_size (if provided) is encoded as a fact,
    allowing Module 1 to distinguish between opening actions and facing a bet.
    """
    facts_added = []
    
    # Position facts
    pos_lower = position.strip().lower().replace("_", " ")
    position_mapping = {
        ("button", "btn"): ("position_Button", True, "position_Big_Blind", False),
        ("big blind", "bb", "bigblind"): ("position_Button", False, "position_Big_Blind", True),
    }
    
    position_found = False
    for valid_positions, (button_fact, button_val, bb_fact, bb_val) in position_mapping.items():
        if pos_lower in valid_positions:
            kb.add_fact(button_fact, button_val)
            kb.add_fact(bb_fact, bb_val)
            facts_added.append(f"{bb_fact} = {bb_val}")
            position_found = True
            break
    
    if not position_found:
        kb.add_fact("position_valid", False)
        facts_added.append("position_valid = False")
        return None, None, facts_added
    
    kb.add_fact("position_valid", True)
    facts_added.append("position_valid = True")
    
    # Hand strength facts
    hand_rank = _get_hand_rank(hand)
    if hand_rank is None:
        return None, None, facts_added
    
    hand_tier = _rank_to_tier(hand_rank)
    
    # Add hand strength category facts
    kb.add_fact("hand_strength_premium", hand_rank <= HAND_STRENGTH_PREMIUM_MAX)
    kb.add_fact("hand_strength_strong", hand_rank <= HAND_STRENGTH_STRONG_MAX)
    kb.add_fact("hand_strength_playable", hand_rank <= HAND_STRENGTH_PLAYABLE_MAX)
    kb.add_fact("hand_strength_marginal", hand_rank <= HAND_STRENGTH_MARGINAL_MAX)
    facts_added.append(f"hand_strength_{hand_tier.lower()} = True (rank {hand_rank})")
    
    # Opponent tendency facts
    opp_lower = opponent_tendency.strip().lower()
    opponent_types = ["Tight", "Loose", "Aggressive", "Passive", "Unknown"]
    for opp_type in opponent_types:
        kb.add_fact(f"opponent_{opp_type}", opp_lower == opp_type.lower())
    
    # Combined opponent facts for rules
    kb.add_fact("opponent_Aggressive_Loose", opp_lower in ("aggressive", "loose"))
    facts_added.append(f"opponent_{opponent_tendency} = True")
    
    # Stack size facts
    kb.add_fact("stack_size_ultra_short", stack_size < STACK_SIZE_ULTRA_SHORT_MAX)
    kb.add_fact(
        "stack_size_short",
        STACK_SIZE_ULTRA_SHORT_MAX <= stack_size < STACK_SIZE_SHORT_MAX,
    )
    kb.add_fact("stack_size_adequate", stack_size >= STACK_SIZE_SHORT_MAX)
    facts_added.append(f"stack_size_adequate = {stack_size >= STACK_SIZE_SHORT_MAX}")

    # Scenario facts: are we facing a bet, and how large is it?
    if opponent_bet_size is not None and opponent_bet_size > 0:
        kb.add_fact("facing_bet", True)
        facts_added.append("facing_bet = True")

        # Very coarse buckets for potential future rules; currently informational.
        # Small bet: up to 3x big blind
        kb.add_fact("bet_size_small", opponent_bet_size <= 3)
        # Medium bet: >3x and up to 6x big blind
        kb.add_fact("bet_size_medium", 3 < opponent_bet_size <= 6)
        # Large bet: >6x big blind
        kb.add_fact("bet_size_large", opponent_bet_size > 6)
    else:
        kb.add_fact("facing_bet", False)
        facts_added.append("facing_bet = False")
    
    return hand_rank, hand_tier, facts_added


def _derive_stack_ok_fallback(kb: KnowledgeBase) -> Tuple[bool, str]:
    """Fallback logic to derive stack_ok if backward chaining fails."""
    stack_size_ultra_short = kb.get_fact("stack_size_ultra_short")
    stack_size_short = kb.get_fact("stack_size_short")
    stack_size_adequate = kb.get_fact("stack_size_adequate")
    hand_strength_premium = kb.get_fact("hand_strength_premium")
    hand_strength_strong = kb.get_fact("hand_strength_strong")
    
    if stack_size_ultra_short and hand_strength_premium:
        kb.add_fact("stack_ok", True)
        return True, "Rule 7 (fallback): ultra-short stack with premium hand → stack_ok"
    elif stack_size_short and hand_strength_strong:
        kb.add_fact("stack_ok", True)
        return True, "Rule 8 (fallback): short stack with strong+ hand → stack_ok"
    elif stack_size_adequate:
        kb.add_fact("stack_ok", True)
        return True, "Rule 9 (fallback): adequate stack → stack_ok"
    else:
        kb.add_fact("stack_ok", False)
        return False, "Rules 7-9 (fallback): stack conditions not met → not stack_ok"


def _derive_playable(kb: KnowledgeBase) -> bool:
    """Derive playable fact based on position, hand strength, and opponent."""
    playable_rules = [
        # (position_fact, opponent_fact, strength_fact, rule_message)
        ("position_Button", "opponent_Tight", "hand_strength_marginal", "Rule 3: Button vs Tight with Marginal+ → playable"),
        ("position_Button", "opponent_Aggressive_Loose", "hand_strength_strong", "Rule 2: Button vs Aggressive/Loose with Strong+ → playable"),
        ("position_Button", "opponent_Passive", "hand_strength_playable", "Rule 4: Button vs Passive with Playable+ → playable"),
        ("position_Button", "opponent_Unknown", "hand_strength_playable", "Rule 5: Button vs Unknown with Playable+ → playable"),
        ("position_Big_Blind", "opponent_Unknown", "hand_strength_strong", "Rule 6: Big Blind vs Unknown with Strong+ → playable"),
    ]
    
    for pos_fact, opp_fact, strength_fact, rule_msg in playable_rules:
        if (kb.get_fact(pos_fact) and 
            kb.get_fact(opp_fact) and 
            kb.get_fact(strength_fact)):
            kb.add_fact("playable", True)
            kb.inference_chain.append(rule_msg)
            return True
    
    kb.add_fact("playable", False)
    kb.inference_chain.append("No rule satisfied → not playable")
    return False


def _derive_final_playable_fallback(kb: KnowledgeBase) -> Tuple[bool, str]:
    """Fallback logic to derive final_playable if backward chaining fails."""
    can_proceed = kb.get_fact("can_proceed")
    stack_ok = kb.get_fact("stack_ok")
    playable = kb.get_fact("playable")
    
    if can_proceed and stack_ok and playable:
        kb.add_fact("final_playable", True)
        return True, "Rule 10 (fallback): can_proceed AND stack_ok AND playable → final_playable"
    else:
        kb.add_fact("final_playable", False)
        return False, "Rule 10 (fallback): conditions not met → not final_playable"


def propositional_logic_hand_decider(
    hand: str,
    position: str,
    stack_size: int,
    opponent_tendency: str,
    opponent_bet_size: Optional[float] = None,
) -> dict:
    """
    Decide hand playability using propositional logic rules with CNF knowledge base.
    
    Args:
        hand: Starting hand (e.g., "Ace-King suited", "AA", "AKs").
        position: Position ("Button" or "Big Blind").
        stack_size: Stack size in big blinds (integer).
        opponent_tendency: "Tight", "Loose", "Aggressive", "Passive", or "Unknown".
        opponent_bet_size: Optional opponent bet size in big blinds.
            - None: opening action (no bet to face)
            - >0: we are facing a bet of this size (e.g., BB facing a raise)
    
    Returns:
        Dict with: playable (bool), reason (str), knowledge_base (dict with CNF rules),
        inference_chain (list).
    """
    # Create knowledge base
    kb = KnowledgeBase()
    
    # Add CNF rules
    for rule in _create_cnf_rules():
        kb.add_rule(rule)
    
    # Derive facts from input (including whether we are facing a bet)
    hand_rank, hand_tier, facts_added = _derive_facts_from_input(
        hand,
        position,
        stack_size,
        opponent_tendency,
        kb,
        opponent_bet_size=opponent_bet_size,
    )
    
    # Check for invalid inputs
    if hand_rank is None:
        hand_norm = _normalize_hand(hand)
        return {
            "playable": False,
            "reason": "Unrecognized hand; cannot evaluate." if hand_norm is None else "Invalid position.",
            "knowledge_base": kb.to_dict(),
            "inference_chain": facts_added,
        }
    
    # Initialize inference chain
    kb.inference_chain = facts_added.copy()
    
    # Apply rules to derive intermediate facts (needed for backward chaining)
    # Rule 1: can_proceed if position_valid
    if kb.get_fact("position_valid"):
        kb.add_fact("can_proceed", True)
        kb.inference_chain.append("Rule 1: position_valid → can_proceed")
    
    # Use backward chaining to derive stack_ok (Rules 7-9)
    kb.inference_chain.append("Using backward chaining to query for stack_ok")
    stack_ok_result, stack_ok_chain = kb.query("stack_ok")
    
    # If backward chaining didn't work, fall back to direct evaluation
    if not stack_ok_result:
        stack_ok_result, fallback_msg = _derive_stack_ok_fallback(kb)
        kb.inference_chain.append(fallback_msg)
    
    # Add backward chaining inference chain for stack_ok
    kb.inference_chain.extend(stack_ok_chain)
    
    # Rules 2-6: playable based on position, hand strength, and opponent
    _derive_playable(kb)
    
    # Use backward chaining to query for final_playable (Rule 10)
    kb.inference_chain.append("Using backward chaining to query for final_playable")
    playable_result, backward_chain = kb.query("final_playable")
    
    # If backward chaining didn't work, fall back to direct evaluation
    if not playable_result:
        playable_result, fallback_msg = _derive_final_playable_fallback(kb)
        kb.inference_chain.append(fallback_msg)
    
    # Add backward chaining inference chain
    kb.inference_chain.extend(backward_chain)
    
    # Build reasoning
    hand_norm = _normalize_hand(hand) or hand
    if playable_result:
        reason = f"Play {hand_norm}: {hand_tier} hand, {position}, {stack_size} BB vs {opponent_tendency}."
    else:
        reason_parts = [f"Hand {hand_norm} ({hand_tier})"]
        if not kb.get_fact("position_valid"):
            reason_parts.append("invalid position")
        elif not kb.get_fact("playable"):
            reason_parts.append(f"too weak for {position} vs {opponent_tendency}")
        elif not kb.get_fact("stack_ok"):
            reason_parts.append(f"stack too short ({stack_size} BB)")
        else:
            reason_parts.append("does not meet playability criteria")
        reason = " ".join(reason_parts) + "."
    
    return {
        "playable": playable_result,
        "reason": reason,
        "knowledge_base": kb.to_dict(),
        "inference_chain": kb.inference_chain,
    }
