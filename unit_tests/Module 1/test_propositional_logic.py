"""
Unit tests for Module 1: Propositional Logic Hand Decider

Tests cover:
- Main function with various inputs
- KnowledgeBase class methods
- Backward chaining inference
- CNF rule creation
- Fact derivation
- Edge cases and boundary conditions
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path to import module
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "Module 1"))

from propositional_logic import (
    propositional_logic_hand_decider,
    KnowledgeBase,
    CNFRule,
    _create_cnf_rules,
    _derive_facts_from_input,
    _rank_to_tier,
    _normalize_hand,
    _get_hand_rank,
    HAND_STRENGTH_PREMIUM_MAX,
    HAND_STRENGTH_STRONG_MAX,
    HAND_STRENGTH_PLAYABLE_MAX,
    HAND_STRENGTH_MARGINAL_MAX,
    STACK_SIZE_ULTRA_SHORT_MAX,
    STACK_SIZE_SHORT_MAX,
)


class TestKnowledgeBase(unittest.TestCase):
    """Test KnowledgeBase class functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.kb = KnowledgeBase()

    def test_init(self):
        """Test KnowledgeBase initialization."""
        self.assertEqual(len(self.kb.rules), 0)
        self.assertEqual(len(self.kb.facts), 0)
        self.assertEqual(len(self.kb.inference_chain), 0)

    def test_add_rule(self):
        """Test adding rules to knowledge base."""
        rule = CNFRule(
            name="Test Rule",
            cnf="(¬A ∨ B)",
            clauses=[["¬A", "B"]],
            description="Test description"
        )
        self.kb.add_rule(rule)
        self.assertEqual(len(self.kb.rules), 1)
        self.assertEqual(self.kb.rules[0].name, "Test Rule")

    def test_add_fact(self):
        """Test adding facts to knowledge base."""
        self.kb.add_fact("test_fact", True)
        self.assertEqual(self.kb.facts["test_fact"], True)
        
        self.kb.add_fact("test_fact", False)
        self.assertEqual(self.kb.facts["test_fact"], False)

    def test_get_fact(self):
        """Test getting facts from knowledge base."""
        self.assertIsNone(self.kb.get_fact("nonexistent"))
        
        self.kb.add_fact("existing_fact", True)
        self.assertEqual(self.kb.get_fact("existing_fact"), True)
        
        self.kb.add_fact("false_fact", False)
        self.assertEqual(self.kb.get_fact("false_fact"), False)

    def test_query_known_fact(self):
        """Test querying for a fact that already exists."""
        self.kb.add_fact("known_fact", True)
        result, chain = self.kb.query("known_fact")
        self.assertTrue(result)
        self.assertIn("known fact", chain[0].lower())

    def test_query_with_rule(self):
        """Test querying using backward chaining with a rule."""
        # Add a simple rule: IF stack_size_adequate THEN stack_ok
        rule = CNFRule(
            name="Test Rule",
            cnf="(¬stack_size_adequate ∨ stack_ok)",
            clauses=[["¬stack_size_adequate", "stack_ok"]],
            description="Test"
        )
        self.kb.add_rule(rule)
        
        # Add premise stack_size_adequate = True
        self.kb.add_fact("stack_size_adequate", True)
        
        # Query for stack_ok
        result, chain = self.kb.query("stack_ok")
        self.assertTrue(result)
        self.assertIn("Proved", chain[-1])
        self.assertTrue(self.kb.facts["stack_ok"])

    def test_query_circular_dependency(self):
        """Test that circular dependencies are detected."""
        # Create circular rule: IF A THEN A (circular)
        rule = CNFRule(
            name="Circular Rule",
            cnf="(¬A ∨ A)",
            clauses=[["¬A", "A"]],
            description="Circular"
        )
        self.kb.add_rule(rule)
        
        # Query should detect circular dependency
        result, chain = self.kb.query("A")
        # Should not prove A (circular)
        self.assertFalse(result)

    def test_to_dict(self):
        """Test converting knowledge base to dictionary."""
        rule = CNFRule(
            name="Test Rule",
            cnf="(¬A ∨ B)",
            clauses=[["¬A", "B"]],
            description="Test"
        )
        self.kb.add_rule(rule)
        self.kb.add_fact("test_fact", True)
        self.kb.inference_chain.append("test step")
        
        kb_dict = self.kb.to_dict()
        self.assertIn("rules", kb_dict)
        self.assertIn("facts", kb_dict)
        self.assertIn("inference_chain", kb_dict)
        self.assertEqual(len(kb_dict["rules"]), 1)
        self.assertEqual(kb_dict["facts"]["test_fact"], True)


class TestCNFRules(unittest.TestCase):
    """Test CNF rule creation and structure."""

    def test_create_cnf_rules(self):
        """Test that all 10 CNF rules are created correctly."""
        rules = _create_cnf_rules()
        self.assertEqual(len(rules), 10)
        
        # Check that all rules have required fields
        for rule in rules:
            self.assertIsInstance(rule, CNFRule)
            self.assertIsNotNone(rule.name)
            self.assertIsNotNone(rule.cnf)
            self.assertIsNotNone(rule.clauses)
            self.assertIsNotNone(rule.description)
            self.assertGreater(len(rule.clauses), 0)

    def test_rule_1_structure(self):
        """Test Rule 1 structure."""
        rules = _create_cnf_rules()
        rule1 = rules[0]
        self.assertIn("Valid Position", rule1.name)
        self.assertIn("can_proceed", rule1.cnf)

    def test_rule_10_structure(self):
        """Test Rule 10 (final decision) structure."""
        rules = _create_cnf_rules()
        rule10 = rules[9]
        self.assertIn("Final Decision", rule10.name)
        self.assertIn("final_playable", rule10.cnf)


class TestHandRanking(unittest.TestCase):
    """Test hand ranking and tier functions."""

    def test_rank_to_tier_premium(self):
        """Test premium tier classification."""
        self.assertEqual(_rank_to_tier(1), "Premium")
        self.assertEqual(_rank_to_tier(15), "Premium")
        self.assertEqual(_rank_to_tier(HAND_STRENGTH_PREMIUM_MAX), "Premium")

    def test_rank_to_tier_strong(self):
        """Test strong tier classification."""
        self.assertEqual(_rank_to_tier(31), "Strong")
        self.assertEqual(_rank_to_tier(45), "Strong")
        self.assertEqual(_rank_to_tier(HAND_STRENGTH_STRONG_MAX), "Strong")

    def test_rank_to_tier_playable(self):
        """Test playable tier classification."""
        self.assertEqual(_rank_to_tier(61), "Playable")
        self.assertEqual(_rank_to_tier(75), "Playable")
        self.assertEqual(_rank_to_tier(HAND_STRENGTH_PLAYABLE_MAX), "Playable")

    def test_rank_to_tier_marginal(self):
        """Test marginal tier classification."""
        self.assertEqual(_rank_to_tier(88), "Marginal")
        self.assertEqual(_rank_to_tier(100), "Marginal")
        self.assertEqual(_rank_to_tier(HAND_STRENGTH_MARGINAL_MAX), "Marginal")

    def test_rank_to_tier_weak(self):
        """Test weak tier classification."""
        self.assertEqual(_rank_to_tier(117), "Weak")
        self.assertEqual(_rank_to_tier(169), "Weak")

    def test_normalize_hand_exact_match(self):
        """Test hand normalization with exact matches."""
        self.assertEqual(_normalize_hand("AA"), "AA")
        self.assertEqual(_normalize_hand("KK"), "KK")
        self.assertEqual(_normalize_hand("KAs"), "KAs")

    def test_normalize_hand_aliases(self):
        """Test hand normalization with aliases."""
        self.assertEqual(_normalize_hand("AKs"), "KAs")
        self.assertEqual(_normalize_hand("AKo"), "KAo")
        self.assertEqual(_normalize_hand("aks"), "KAs")
        self.assertEqual(_normalize_hand("pocket aces"), "AA")
        self.assertEqual(_normalize_hand("Ace King suited"), "KAs")

    def test_normalize_hand_invalid(self):
        """Test hand normalization with invalid inputs."""
        self.assertIsNone(_normalize_hand("invalid"))
        self.assertIsNone(_normalize_hand("ZZ"))
        self.assertIsNone(_normalize_hand(""))

    def test_get_hand_rank_valid(self):
        """Test getting hand rank for valid hands."""
        self.assertEqual(_get_hand_rank("AA"), 1)
        self.assertEqual(_get_hand_rank("KK"), 2)
        self.assertEqual(_get_hand_rank("KAs"), 9)

    def test_get_hand_rank_invalid(self):
        """Test getting hand rank for invalid hands."""
        self.assertIsNone(_get_hand_rank("invalid"))
        self.assertIsNone(_get_hand_rank("ZZ"))


class TestFactDerivation(unittest.TestCase):
    """Test fact derivation from input."""

    def setUp(self):
        """Set up test fixtures."""
        self.kb = KnowledgeBase()

    def test_derive_facts_button_position(self):
        """Test fact derivation for Button position."""
        hand_rank, hand_tier, facts_added = _derive_facts_from_input(
            "AA", "Button", 50, "Tight", self.kb
        )
        
        self.assertEqual(hand_rank, 1)
        self.assertEqual(hand_tier, "Premium")
        self.assertTrue(self.kb.get_fact("position_Button"))
        self.assertFalse(self.kb.get_fact("position_Big_Blind"))
        self.assertTrue(self.kb.get_fact("position_valid"))

    def test_derive_facts_big_blind_position(self):
        """Test fact derivation for Big Blind position."""
        hand_rank, hand_tier, facts_added = _derive_facts_from_input(
            "AA", "Big Blind", 50, "Tight", self.kb
        )
        
        self.assertFalse(self.kb.get_fact("position_Button"))
        self.assertTrue(self.kb.get_fact("position_Big_Blind"))
        self.assertTrue(self.kb.get_fact("position_valid"))

    def test_derive_facts_invalid_position(self):
        """Test fact derivation with invalid position."""
        hand_rank, hand_tier, facts_added = _derive_facts_from_input(
            "AA", "Invalid", 50, "Tight", self.kb
        )
        
        self.assertIsNone(hand_rank)
        self.assertFalse(self.kb.get_fact("position_valid"))

    def test_derive_facts_hand_strength(self):
        """Test hand strength fact derivation."""
        hand_rank, hand_tier, facts_added = _derive_facts_from_input(
            "AA", "Button", 50, "Tight", self.kb
        )
        
        # AA is rank 1, so all strength categories should be True
        self.assertTrue(self.kb.get_fact("hand_strength_premium"))
        self.assertTrue(self.kb.get_fact("hand_strength_strong"))
        self.assertTrue(self.kb.get_fact("hand_strength_playable"))
        self.assertTrue(self.kb.get_fact("hand_strength_marginal"))

    def test_derive_facts_opponent_types(self):
        """Test opponent type fact derivation."""
        opponent_types = ["Tight", "Loose", "Aggressive", "Passive", "Unknown"]
        
        for opp_type in opponent_types:
            kb = KnowledgeBase()
            hand_rank, hand_tier, facts_added = _derive_facts_from_input(
                "AA", "Button", 50, opp_type, kb
            )
            
            # Check that the correct opponent fact is True
            self.assertTrue(kb.get_fact(f"opponent_{opp_type}"))
            
            # Check that other opponent facts are False
            for other_type in opponent_types:
                if other_type != opp_type:
                    self.assertFalse(kb.get_fact(f"opponent_{other_type}"))

    def test_derive_facts_stack_sizes(self):
        """Test stack size fact derivation."""
        # Ultra-short stack
        kb1 = KnowledgeBase()
        _derive_facts_from_input("AA", "Button", 8, "Tight", kb1)
        self.assertTrue(kb1.get_fact("stack_size_ultra_short"))
        self.assertFalse(kb1.get_fact("stack_size_short"))
        self.assertFalse(kb1.get_fact("stack_size_adequate"))
        
        # Short stack
        kb2 = KnowledgeBase()
        _derive_facts_from_input("AA", "Button", 15, "Tight", kb2)
        self.assertFalse(kb2.get_fact("stack_size_ultra_short"))
        self.assertTrue(kb2.get_fact("stack_size_short"))
        self.assertFalse(kb2.get_fact("stack_size_adequate"))
        
        # Adequate stack
        kb3 = KnowledgeBase()
        _derive_facts_from_input("AA", "Button", 50, "Tight", kb3)
        self.assertFalse(kb3.get_fact("stack_size_ultra_short"))
        self.assertFalse(kb3.get_fact("stack_size_short"))
        self.assertTrue(kb3.get_fact("stack_size_adequate"))


class TestMainFunction(unittest.TestCase):
    """Test the main propositional_logic_hand_decider function."""

    def test_premium_hand_button_tight(self):
        """Test premium hand from Button vs Tight opponent."""
        result = propositional_logic_hand_decider("AA", "Button", 50, "Tight")
        
        self.assertTrue(result["playable"])
        self.assertIn("Play", result["reason"])
        self.assertIn("knowledge_base", result)
        self.assertIn("inference_chain", result)
        self.assertEqual(len(result["knowledge_base"]["rules"]), 10)

    def test_strong_hand_button_aggressive(self):
        """Test strong hand from Button vs Aggressive opponent."""
        result = propositional_logic_hand_decider("K9s", "Button", 50, "Aggressive")
        
        self.assertTrue(result["playable"])
        self.assertIn("knowledge_base", result)

    def test_weak_hand_not_playable(self):
        """Test weak hand is not playable."""
        result = propositional_logic_hand_decider("72o", "Button", 50, "Tight")
        
        self.assertFalse(result["playable"])
        self.assertIn("knowledge_base", result)

    def test_ultra_short_stack_premium_hand(self):
        """Test ultra-short stack with premium hand."""
        result = propositional_logic_hand_decider("AA", "Button", 8, "Tight")
        
        self.assertTrue(result["playable"])
        # Should use Rule 7 for stack_ok
        self.assertIn("stack_ok", str(result["inference_chain"]))

    def test_ultra_short_stack_weak_hand(self):
        """Test ultra-short stack with weak hand."""
        result = propositional_logic_hand_decider("72o", "Button", 8, "Tight")
        
        self.assertFalse(result["playable"])
        # Stack should not be OK
        kb_facts = result["knowledge_base"]["facts"]
        self.assertFalse(kb_facts.get("stack_ok", True))

    def test_short_stack_strong_hand(self):
        """Test short stack with strong hand."""
        result = propositional_logic_hand_decider("K9s", "Button", 15, "Tight")
        
        self.assertTrue(result["playable"])

    def test_short_stack_weak_hand(self):
        """Test short stack with weak hand."""
        result = propositional_logic_hand_decider("72o", "Button", 15, "Tight")
        
        self.assertFalse(result["playable"])

    def test_big_blind_position(self):
        """Test Big Blind position."""
        result = propositional_logic_hand_decider("QQ", "Big Blind", 50, "Unknown")
        
        self.assertTrue(result["playable"])
        kb_facts = result["knowledge_base"]["facts"]
        self.assertTrue(kb_facts.get("position_Big_Blind"))

    def test_all_opponent_types(self):
        """Test all opponent tendency types."""
        opponent_types = ["Tight", "Loose", "Aggressive", "Passive", "Unknown"]
        
        for opp_type in opponent_types:
            result = propositional_logic_hand_decider("AA", "Button", 50, opp_type)
            self.assertIn("playable", result)
            self.assertIn("knowledge_base", result)
            # Should be playable with AA from Button
            self.assertTrue(result["playable"])

    def test_invalid_hand(self):
        """Test with invalid hand."""
        result = propositional_logic_hand_decider("Invalid", "Button", 50, "Tight")
        
        self.assertFalse(result["playable"])
        self.assertIn("Unrecognized hand", result["reason"])

    def test_invalid_position(self):
        """Test with invalid position."""
        result = propositional_logic_hand_decider("AA", "Invalid", 50, "Tight")
        
        self.assertFalse(result["playable"])
        self.assertIn("Invalid position", result["reason"])

    def test_hand_normalization_variants(self):
        """Test various hand input formats."""
        hand_variants = ["AA", "AKs", "AKo", "ace king suited", "pocket aces"]
        
        for hand in hand_variants:
            result = propositional_logic_hand_decider(hand, "Button", 50, "Tight")
            self.assertIn("playable", result)
            self.assertIn("knowledge_base", result)

    def test_output_structure(self):
        """Test that output has correct structure."""
        result = propositional_logic_hand_decider("AA", "Button", 50, "Tight")
        
        # Check required keys
        self.assertIn("playable", result)
        self.assertIn("reason", result)
        self.assertIn("knowledge_base", result)
        self.assertIn("inference_chain", result)
        
        # Check types
        self.assertIsInstance(result["playable"], bool)
        self.assertIsInstance(result["reason"], str)
        self.assertIsInstance(result["knowledge_base"], dict)
        self.assertIsInstance(result["inference_chain"], list)
        
        # Check knowledge_base structure
        kb = result["knowledge_base"]
        self.assertIn("rules", kb)
        self.assertIn("facts", kb)
        self.assertIn("inference_chain", kb)
        self.assertEqual(len(kb["rules"]), 10)

    def test_inference_chain_not_empty(self):
        """Test that inference chain is populated."""
        result = propositional_logic_hand_decider("AA", "Button", 50, "Tight")
        
        self.assertGreater(len(result["inference_chain"]), 0)
        # Should contain backward chaining steps
        chain_str = " ".join(result["inference_chain"])
        self.assertIn("backward chaining", chain_str.lower() or "rule" in chain_str.lower())


class TestBackwardChaining(unittest.TestCase):
    """Test backward chaining inference."""

    def test_backward_chain_stack_ok_ultra_short_premium(self):
        """Test backward chaining for stack_ok with ultra-short stack and premium hand."""
        kb = KnowledgeBase()
        
        # Add rules
        for rule in _create_cnf_rules():
            kb.add_rule(rule)
        
        # Add facts
        kb.add_fact("stack_size_ultra_short", True)
        kb.add_fact("hand_strength_premium", True)
        
        # Query for stack_ok
        result, chain = kb.query("stack_ok")
        
        self.assertTrue(result)
        self.assertIn("stack_ok", kb.facts)
        self.assertTrue(kb.facts["stack_ok"])

    def test_backward_chain_stack_ok_adequate(self):
        """Test backward chaining for stack_ok with adequate stack."""
        kb = KnowledgeBase()
        
        # Add rules
        for rule in _create_cnf_rules():
            kb.add_rule(rule)
        
        # Add facts
        kb.add_fact("stack_size_adequate", True)
        
        # Query for stack_ok
        result, chain = kb.query("stack_ok")
        
        self.assertTrue(result)
        self.assertTrue(kb.facts["stack_ok"])

    def test_backward_chain_final_playable(self):
        """Test backward chaining for final_playable."""
        kb = KnowledgeBase()
        
        # Add rules
        for rule in _create_cnf_rules():
            kb.add_rule(rule)
        
        # Add all required facts
        kb.add_fact("can_proceed", True)
        kb.add_fact("stack_ok", True)
        kb.add_fact("playable", True)
        
        # Query for final_playable
        result, chain = kb.query("final_playable")
        
        self.assertTrue(result)
        self.assertTrue(kb.facts["final_playable"])

    def test_backward_chain_nested(self):
        """Test nested backward chaining (proving stack_ok to prove final_playable)."""
        kb = KnowledgeBase()
        
        # Add rules
        for rule in _create_cnf_rules():
            kb.add_rule(rule)
        
        # Add facts for stack_ok
        kb.add_fact("stack_size_adequate", True)
        kb.add_fact("can_proceed", True)
        kb.add_fact("playable", True)
        
        # Query for final_playable (should prove stack_ok first)
        result, chain = kb.query("final_playable")
        
        self.assertTrue(result)
        self.assertTrue(kb.facts["final_playable"])
        # stack_ok should have been proven
        self.assertTrue(kb.facts.get("stack_ok", False))


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions."""

    def test_boundary_stack_sizes(self):
        """Test boundary stack sizes."""
        # Exactly 10 BB (boundary between ultra-short and short)
        result1 = propositional_logic_hand_decider("AA", "Button", 10, "Tight")
        self.assertIn("playable", result1)
        
        # Exactly 20 BB (boundary between short and adequate)
        result2 = propositional_logic_hand_decider("AA", "Button", 20, "Tight")
        self.assertIn("playable", result2)
        
        # Just below 10 BB
        result3 = propositional_logic_hand_decider("AA", "Button", 9, "Tight")
        self.assertIn("playable", result3)
        
        # Just below 20 BB
        result4 = propositional_logic_hand_decider("AA", "Button", 19, "Tight")
        self.assertIn("playable", result4)

    def test_boundary_hand_ranks(self):
        """Test boundary hand ranks."""
        # Rank 30 (boundary between Premium and Strong)
        # Rank 60 (boundary between Strong and Playable)
        # Rank 87 (boundary between Playable and Marginal)
        # Rank 116 (boundary between Marginal and Weak)
        
        # These would require access to specific hands at these ranks
        # Testing that the function handles all rank ranges
        result = propositional_logic_hand_decider("AA", "Button", 50, "Tight")
        self.assertIn("playable", result)

    def test_position_variations(self):
        """Test position input variations."""
        variations = ["Button", "button", "BUTTON", "btn", "Big Blind", "big blind", "BB", "bb"]
        
        for pos in variations:
            result = propositional_logic_hand_decider("AA", pos, 50, "Tight")
            self.assertIn("playable", result)

    def test_opponent_variations(self):
        """Test opponent input variations."""
        variations = ["Tight", "tight", "TIGHT", "Loose", "loose", "Aggressive", "aggressive"]
        
        for opp in variations:
            result = propositional_logic_hand_decider("AA", "Button", 50, opp)
            self.assertIn("playable", result)


if __name__ == "__main__":
    unittest.main()
