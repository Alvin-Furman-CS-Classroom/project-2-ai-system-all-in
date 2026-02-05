"""
Rule-based hand playability using propositional logic.
Rules combine hand strength, position, stack size, and opponent tendency.
Implements knowledge base with CNF-encoded rules and inference methods.
"""

from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass

# Ordered list of 169 hands (rank 1 = best), matching POKER_HAND_WIN_PERCENTAGES.md.
# Tier: 1-30 Premium, 31-60 Strong, 61-87 Playable, 88-116 Marginal, 117-169 Weak.
HAND_RANK_LIST = [
    "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "KAs", "QAs", "JAs", "KAo", "QAo", "TAs", "66", "JAo", "QKs", "9As", "TAo", "JKs", "8As", "TKs", "5As", "QKo", "9Ao", "JKo", "7As", "TKo", "JQs", "6As",
    "8Ao", "4As", "55", "9Ks", "3As", "6Ao", "8Ks", "TQs", "JQo", "2As", "9Ko", "9Qs", "TJs", "7Ks", "5Ao", "4Ao", "7Ao", "6Ks", "44", "TQo", "7Ko", "3Ao", "9Qo", "8Qs", "8Ko", "9Js", "TJo", "5Ks", "2Ao", "6Ko",
    "4Ks", "33", "8Js", "7Qs", "9Jo", "5Ko", "3Ks", "8Qo", "9Ts", "5Qs", "2Ks", "6Qs", "9To", "7Js", "3Ko", "3Qs", "4Qs", "8Ts", "4Ko", "8Jo", "6Qo", "6Js", "2Qs", "7Qo", "89s", "22", "2Ko", "7Ts",
    "5Js", "8To", "4Js", "5Qo", "7Jo", "4Qo", "79s", "6Ts", "3Qo", "7To", "3Js", "6Jo", "89o", "5Jo", "2Js", "69s", "5Ts", "2Qo", "78s", "68s", "79o", "4Ts", "6To", "4Jo", "3Jo", "59s", "67s", "3Ts",
    "2Ts", "2Jo", "78o", "58s", "5To", "69o", "49s", "57s", "39s", "4To", "48s", "29s", "56s", "3To", "68o", "59o", "67o", "47s", "45s", "58o", "2To", "49o", "38s", "57o", "39o", "46s", "35s", "28s", "37s", "29o", "56o", "34s", "36s", "48o", "47o", "45o", "46o", "27s", "25s", "26s", "24s", "37o", "28o", "38o", "36o", "35o", "34o", "23s", "27o", "25o", "26o", "24o", "23o",
]


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
    
    def forward_chain(self) -> Tuple[Dict[str, bool], List[str]]:
        """
        Forward chaining inference: derive new facts from rules and existing facts.
        Returns updated facts and inference chain.
        
        For CNF rule (¬A ∨ B): if A is true, then B must be true.
        For CNF rule (A ∨ B): at least one must be true.
        """
        chain = []
        changed = True
        
        while changed:
            changed = False
            for rule in self.rules:
                # Evaluate all clauses in the rule (CNF: all clauses must be satisfied)
                all_clauses_satisfied = True
                for clause in rule.clauses:
                    if not self._evaluate_clause(clause):
                        all_clauses_satisfied = False
                        break
                
                if all_clauses_satisfied:
                    # Rule is satisfied, try to derive conclusions
                    for clause in rule.clauses:
                        # For CNF clause (¬A ∨ B), if A is true, derive B
                        for i, literal in enumerate(clause):
                            if literal.startswith("¬"):
                                fact = literal[1:]
                                if fact in self.facts and self.facts[fact]:
                                    # A is true, so derive the positive literal (B)
                                    for other_literal in clause:
                                        if not other_literal.startswith("¬") and other_literal != fact:
                                            if other_literal not in self.facts:
                                                self.facts[other_literal] = True
                                                chain.append(f"Applied {rule.name}: {fact}=True → derived {other_literal}=True")
                                                changed = True
                        else:
                            # Positive literal - if all negated literals are false, this is true
                            negated_all_false = True
                            for other_literal in clause:
                                if other_literal.startswith("¬"):
                                    negated_fact = other_literal[1:]
                                    if negated_fact in self.facts and self.facts[negated_fact]:
                                        negated_all_false = False
                                        break
                            
                            if negated_all_false and literal not in self.facts:
                                self.facts[literal] = True
                                chain.append(f"Applied {rule.name}: derived {literal}=True")
                                changed = True
        
        return self.facts.copy(), chain
    
    def _evaluate_clause(self, clause: List[str]) -> bool:
        """Evaluate a CNF clause (disjunction) given current facts."""
        # Clause is OR of literals, so true if any literal is true
        for literal in clause:
            if literal.startswith("¬"):
                # Negated literal
                fact = literal[1:]
                if fact in self.facts and not self.facts[fact]:
                    return True
            else:
                # Positive literal
                if literal in self.facts and self.facts[literal]:
                    return True
        return False
    
    def _extract_conclusion(self, rule: CNFRule) -> Optional[str]:
        """Extract conclusion from rule (e.g., 'playable' from CNF rule)."""
        # Look for 'playable' or other conclusions in the rule
        for clause in rule.clauses:
            for literal in clause:
                if not literal.startswith("¬") and literal in ["playable", "not_playable"]:
                    return literal
        return None
    
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
                # Check if rule's premises are satisfied
                premises_satisfied = True
                premise_chain = []
                
                for clause in rule.clauses:
                    clause_satisfied = False
                    for literal in clause:
                        if literal == goal:
                            continue  # Skip the conclusion itself
                        
                        if literal.startswith("¬"):
                            fact = literal[1:]
                            result, sub_chain = self._backward_chain(fact, visited.copy())
                            if not result:  # Negated fact is true if fact is false
                                clause_satisfied = True
                                premise_chain.extend(sub_chain)
                                break
                        else:
                            result, sub_chain = self._backward_chain(literal, visited.copy())
                            if result:
                                clause_satisfied = True
                                premise_chain.extend(sub_chain)
                                break
                    
                    if not clause_satisfied:
                        premises_satisfied = False
                        break
                
                if premises_satisfied:
                    self.facts[goal] = True
                    chain.extend(premise_chain)
                    chain.append(f"Proved '{goal}' using {rule.name}")
                    return True, chain
        
        return False, chain + [f"Cannot prove '{goal}'"]
    
    def _get_conclusions(self, rule: CNFRule) -> List[str]:
        """Extract all conclusions from a rule."""
        conclusions = []
        for clause in rule.clauses:
            for literal in clause:
                if not literal.startswith("¬") and literal in ["playable", "not_playable"]:
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
    if rank <= 30:
        return "Premium"
    if rank <= 60:
        return "Strong"
    if rank <= 87:
        return "Playable"
    if rank <= 116:
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
    # IF position_valid THEN (can proceed), else not_playable
    # CNF: (¬position_valid ∨ can_proceed) ∧ (position_valid ∨ not_playable)
    rules.append(CNFRule(
        name="Rule 1: Valid Position",
        cnf="(¬position_valid ∨ can_proceed) ∧ (position_valid ∨ not_playable)",
        clauses=[
            ["¬position_valid", "can_proceed"],
            ["position_valid", "not_playable"]
        ],
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
    # IF (stack_size < 10 ∧ hand_strength_premium) THEN playable
    # CNF: (stack_size_adequate ∨ hand_strength_premium ∨ playable)
    # Actually: (¬stack_size_ultra_short ∨ ¬hand_strength_premium ∨ playable)
    rules.append(CNFRule(
        name="Rule 7: Ultra-Short Stack Premium",
        cnf="(¬stack_size_ultra_short ∨ ¬hand_strength_premium ∨ playable)",
        clauses=[["¬stack_size_ultra_short", "¬hand_strength_premium", "playable"]],
        description="Ultra-short stack (<10 BB) requires Premium hands"
    ))
    
    # Rule 8: Stack size for short stack
    # IF (stack_size < 20 ∧ hand_strength_strong_or_better) THEN playable
    # CNF: (¬stack_size_short ∨ ¬hand_strength_strong ∨ playable)
    rules.append(CNFRule(
        name="Rule 8: Short Stack Strong",
        cnf="(¬stack_size_short ∨ ¬hand_strength_strong ∨ playable)",
        clauses=[["¬stack_size_short", "¬hand_strength_strong", "playable"]],
        description="Short stack (10-20 BB) requires Strong+ hands"
    ))
    
    # Rule 9: Adequate stack allows all playable hands
    # IF (stack_size_adequate ∧ can_proceed) THEN (stack_ok)
    # CNF: (¬stack_size_adequate ∨ ¬can_proceed ∨ stack_ok)
    rules.append(CNFRule(
        name="Rule 9: Adequate Stack",
        cnf="(¬stack_size_adequate ∨ ¬can_proceed ∨ stack_ok)",
        clauses=[["¬stack_size_adequate", "¬can_proceed", "stack_ok"]],
        description="Adequate stack (≥20 BB) allows all playable hands"
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
    kb: KnowledgeBase
) -> Tuple[Optional[int], Optional[str], List[str]]:
    """Derive facts from input and add to knowledge base. Returns (hand_rank, hand_tier, facts_added)."""
    facts_added = []
    
    # Position facts
    pos_lower = position.strip().lower().replace("_", " ")
    if pos_lower in ("button", "btn"):
        kb.add_fact("position_Button", True)
        kb.add_fact("position_Big_Blind", False)
        facts_added.append("position_Button = True")
    elif pos_lower in ("big blind", "bb", "bigblind"):
        kb.add_fact("position_Button", False)
        kb.add_fact("position_Big_Blind", True)
        facts_added.append("position_Big_Blind = True")
    else:
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
    kb.add_fact("hand_strength_premium", hand_rank <= 30)
    kb.add_fact("hand_strength_strong", hand_rank <= 60)
    kb.add_fact("hand_strength_playable", hand_rank <= 87)
    kb.add_fact("hand_strength_marginal", hand_rank <= 116)
    facts_added.append(f"hand_strength_{hand_tier.lower()} = True (rank {hand_rank})")
    
    # Opponent tendency facts
    opp_lower = opponent_tendency.strip().lower()
    kb.add_fact("opponent_Tight", opp_lower == "tight")
    kb.add_fact("opponent_Loose", opp_lower == "loose")
    kb.add_fact("opponent_Aggressive", opp_lower == "aggressive")
    kb.add_fact("opponent_Passive", opp_lower == "passive")
    kb.add_fact("opponent_Unknown", opp_lower == "unknown")
    
    # Combined opponent facts for rules
    kb.add_fact("opponent_Aggressive_Loose", opp_lower in ("aggressive", "loose"))
    facts_added.append(f"opponent_{opponent_tendency} = True")
    
    # Stack size facts
    kb.add_fact("stack_size_ultra_short", stack_size < 10)
    kb.add_fact("stack_size_short", 10 <= stack_size < 20)
    kb.add_fact("stack_size_adequate", stack_size >= 20)
    facts_added.append(f"stack_size_adequate = {stack_size >= 20}")
    
    return hand_rank, hand_tier, facts_added


def first_order_logic_hand_decider(
    hand: str,
    position: str,
    stack_size: int,
    opponent_tendency: str,
) -> dict:
    """
    Decide hand playability using propositional logic rules with CNF knowledge base.
    
    Args:
        hand: Starting hand (e.g., "Ace-King suited", "AA", "AKs").
        position: Position ("Button" or "Big Blind").
        stack_size: Stack size in big blinds (integer).
        opponent_tendency: "Tight", "Loose", "Aggressive", "Passive", or "Unknown".
    
    Returns:
        Dict with: playable (bool), reason (str), knowledge_base (dict with CNF rules),
        hand_normalized (Optional[str]), hand_rank (Optional[int]), hand_tier (Optional[str]),
        inference_chain (list).
    """
    # Create knowledge base
    kb = KnowledgeBase()
    
    # Add CNF rules
    rules = _create_cnf_rules()
    for rule in rules:
        kb.add_rule(rule)
    
    # Derive facts from input
    hand_rank, hand_tier, facts_added = _derive_facts_from_input(
        hand, position, stack_size, opponent_tendency, kb
    )
    
    # Check for invalid inputs
    if hand_rank is None:
        hand_norm = _normalize_hand(hand)
        return {
            "playable": False,
            "reason": "Unrecognized hand; cannot evaluate." if hand_norm is None else "Invalid position.",
            "knowledge_base": kb.to_dict(),
            "hand_normalized": hand_norm,
            "hand_rank": None,
            "hand_tier": None,
            "inference_chain": facts_added,
        }
    
    hand_norm = _normalize_hand(hand) or hand
    
    # Forward chaining inference
    updated_facts, forward_chain = kb.forward_chain()
    kb.facts = updated_facts
    kb.inference_chain = facts_added + forward_chain
    
    # Apply rules to derive intermediate facts
    # Rule 1: can_proceed if position_valid
    if kb.get_fact("position_valid"):
        kb.add_fact("can_proceed", True)
        kb.inference_chain.append("Rule 1: position_valid → can_proceed")
    
    # Rule 7-9: stack_ok based on stack size and hand strength
    if stack_size < 10:
        if kb.get_fact("hand_strength_premium"):
            kb.add_fact("stack_ok", True)
            kb.inference_chain.append("Rule 7: ultra-short stack with premium hand → stack_ok")
        else:
            kb.add_fact("stack_ok", False)
            kb.inference_chain.append("Rule 7: ultra-short stack requires premium hand")
    elif stack_size < 20:
        if kb.get_fact("hand_strength_strong"):
            kb.add_fact("stack_ok", True)
            kb.inference_chain.append("Rule 8: short stack with strong+ hand → stack_ok")
        else:
            kb.add_fact("stack_ok", False)
            kb.inference_chain.append("Rule 8: short stack requires strong+ hand")
    else:
        kb.add_fact("stack_ok", True)
        kb.inference_chain.append("Rule 9: adequate stack → stack_ok")
    
    # Rules 2-6: playable based on position, hand strength, and opponent
    playable_derived = False
    if kb.get_fact("position_Button"):
        if kb.get_fact("opponent_Tight") and kb.get_fact("hand_strength_marginal"):
            kb.add_fact("playable", True)
            kb.inference_chain.append("Rule 3: Button vs Tight with Marginal+ → playable")
            playable_derived = True
        elif kb.get_fact("opponent_Aggressive_Loose") and kb.get_fact("hand_strength_strong"):
            kb.add_fact("playable", True)
            kb.inference_chain.append("Rule 2: Button vs Aggressive/Loose with Strong+ → playable")
            playable_derived = True
        elif kb.get_fact("opponent_Passive") and kb.get_fact("hand_strength_playable"):
            kb.add_fact("playable", True)
            kb.inference_chain.append("Rule 4: Button vs Passive with Playable+ → playable")
            playable_derived = True
        elif kb.get_fact("opponent_Unknown") and kb.get_fact("hand_strength_playable"):
            kb.add_fact("playable", True)
            kb.inference_chain.append("Rule 5: Button vs Unknown with Playable+ → playable")
            playable_derived = True
    
    if kb.get_fact("position_Big_Blind") and kb.get_fact("opponent_Unknown") and kb.get_fact("hand_strength_strong"):
        kb.add_fact("playable", True)
        kb.inference_chain.append("Rule 6: Big Blind vs Unknown with Strong+ → playable")
        playable_derived = True
    
    if not playable_derived:
        kb.add_fact("playable", False)
        kb.inference_chain.append("No rule satisfied → not playable")
    
    # Rule 10: final_playable = can_proceed AND stack_ok AND playable
    can_proceed = kb.get_fact("can_proceed")
    stack_ok = kb.get_fact("stack_ok")
    playable = kb.get_fact("playable")
    
    if can_proceed and stack_ok and playable:
        playable_result = True
        kb.add_fact("final_playable", True)
        kb.inference_chain.append("Rule 10: can_proceed AND stack_ok AND playable → final_playable")
    else:
        playable_result = False
        kb.add_fact("final_playable", False)
        kb.inference_chain.append("Rule 10: conditions not met → not final_playable")
    
    # Build reasoning
    if playable_result:
        reason = f"Play {hand_norm}: {hand_tier} hand, {position}, {stack_size} BB vs {opponent_tendency}."
    else:
        reason_parts = [f"Hand {hand_norm} ({hand_tier})"]
        if kb.get_fact("position_valid") is False:
            reason_parts.append("invalid position")
        elif kb.get_fact("playable") is not True:
            reason_parts.append(f"too weak for {position} vs {opponent_tendency}")
        elif kb.get_fact("stack_ok") is False or kb.get_fact("stack_size_adequate") is False:
            reason_parts.append(f"stack too short ({stack_size} BB)")
        else:
            reason_parts.append("does not meet playability criteria")
        reason = " ".join(reason_parts) + "."
    
    return {
        "playable": playable_result,
        "reason": reason,
        "knowledge_base": kb.to_dict(),
        "hand_normalized": hand_norm,
        "hand_rank": hand_rank,
        "hand_tier": hand_tier,
        "inference_chain": kb.inference_chain,
    }
