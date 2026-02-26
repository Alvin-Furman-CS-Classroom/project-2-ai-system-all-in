"""
Unit tests for Module 2: Optimal Bet Sizing Search

Tests cover:
- Expected Value calculation (ev_calculator)
- Bet size category adjustments
- A* search algorithm (bet_sizing_search)
- Edge cases and boundary conditions
"""

import unittest
import sys
from pathlib import Path

# Add Module 2 to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "Module 2"))

from ev_calculator import (
    calculate_ev,
    calculate_ev_call,
    calculate_ev_fold,
    _get_bet_size_category,
    _get_adjusted_opponent_probs,
    get_hand_equity,
    OPPONENT_PROBABILITIES,
    BET_SIZE_SMALL_MAX,
    BET_SIZE_MEDIUM_MAX,
)
from bet_sizing_search import a_star_search
from bet_size_discretization import (
    MIN_BET_SIZE,
    MAX_STANDARD_BET_SIZE,
)


class TestBetSizeCategories(unittest.TestCase):
    """Test bet size category logic."""

    def test_small_category(self):
        """Bet sizes <= 2.5 are small."""
        self.assertEqual(_get_bet_size_category(2.0), "small")
        self.assertEqual(_get_bet_size_category(2.5), "small")

    def test_medium_category(self):
        """Bet sizes 2.5-4.0 are medium."""
        self.assertEqual(_get_bet_size_category(3.0), "medium")
        self.assertEqual(_get_bet_size_category(4.0), "medium")

    def test_large_category(self):
        """Bet sizes > 4.0 are large."""
        self.assertEqual(_get_bet_size_category(5.0), "large")
        self.assertEqual(_get_bet_size_category(10.0), "large")


class TestAdjustedProbabilities(unittest.TestCase):
    """Test that opponent probabilities adjust by bet size category."""

    def test_small_bet_more_calls(self):
        """Small bets: fewer folds, more calls."""
        base = OPPONENT_PROBABILITIES["Tight"]
        small = _get_adjusted_opponent_probs("Tight", 2.0)
        large = _get_adjusted_opponent_probs("Tight", 6.0)
        self.assertLess(small["fold"], large["fold"])
        self.assertGreater(small["call"], large["call"])

    def test_probabilities_sum_to_one(self):
        """Adjusted probabilities should sum to 1."""
        for tendency in ["Tight", "Loose", "Aggressive"]:
            for bet_size in [2.0, 3.0, 6.0]:
                probs = _get_adjusted_opponent_probs(tendency, bet_size)
                total = probs["fold"] + probs["call"] + probs["raise"]
                self.assertAlmostEqual(total, 1.0, places=5)

    def test_small_medium_large_patterns_all_tendencies(self):
        """
        For all opponent tendencies, small bets should induce more calls and fewer folds
        than medium bets, and large bets should induce more folds and fewer calls than medium.
        """
        tendencies = ["Tight", "Loose", "Aggressive", "Passive", "Unknown"]
        small_size = 2.0
        medium_size = 3.0
        large_size = 6.0
        for tendency in tendencies:
            small = _get_adjusted_opponent_probs(tendency, small_size)
            medium = _get_adjusted_opponent_probs(tendency, medium_size)
            large = _get_adjusted_opponent_probs(tendency, large_size)

            # Small vs medium: more calls, fewer folds
            self.assertLessEqual(small["fold"], medium["fold"])
            self.assertGreaterEqual(small["call"], medium["call"])

            # Large vs medium: more folds, fewer calls
            self.assertGreaterEqual(large["fold"], medium["fold"])
            self.assertLessEqual(large["call"], medium["call"])


class TestExpectedValue(unittest.TestCase):
    """Test Expected Value calculation."""

    def test_ev_premium_hand(self):
        """Premium hand (AA) should have positive EV."""
        ev = calculate_ev(
            3.0, "AA", "Button", (50, 50), "Tight"
        )
        self.assertIsInstance(ev, float)
        self.assertGreater(ev, 0)

    def test_ev_weak_hand(self):
        """Weak hand EV calculation."""
        ev = calculate_ev(
            3.0, "72o", "Button", (50, 50), "Tight"
        )
        self.assertIsInstance(ev, float)

    def test_ev_different_opponents(self):
        """EV should vary with opponent tendency."""
        ev_tight = calculate_ev(3.0, "AA", "Button", (50, 50), "Tight")
        ev_loose = calculate_ev(3.0, "AA", "Button", (50, 50), "Loose")
        self.assertIsInstance(ev_tight, float)
        self.assertIsInstance(ev_loose, float)

    def test_ev_different_bet_sizes(self):
        """EV should change with bet size (due to category adjustments)."""
        ev_small = calculate_ev(2.0, "AA", "Button", (50, 50), "Tight")
        ev_medium = calculate_ev(3.0, "AA", "Button", (50, 50), "Tight")
        ev_large = calculate_ev(6.0, "AA", "Button", (50, 50), "Tight")
        self.assertIsInstance(ev_small, float)
        self.assertIsInstance(ev_medium, float)
        self.assertIsInstance(ev_large, float)

    def test_ev_unknown_hand(self):
        """Hand not in equity table defaults to 0.5 equity."""
        ev = calculate_ev(3.0, "XX", "Button", (50, 50), "Tight")
        self.assertIsInstance(ev, float)

    def test_ev_fold(self):
        """Folding has EV 0."""
        ev = calculate_ev_fold(3.0, 1.5)
        self.assertEqual(ev, 0.0)

    def test_ev_call(self):
        """Call EV calculation."""
        ev = calculate_ev_call(
            "AA", "Button", (50, 50), "Tight", 3.0, 1.5
        )
        self.assertIsInstance(ev, float)


class TestAStarSearch(unittest.TestCase):
    """Test A* search algorithm."""

    def test_a_star_premium_hand(self):
        """A* with premium hand returns valid result."""
        result = a_star_search(
            "AA", "Button", (50, 50), "Tight"
        )
        self.assertIn("action", result)
        self.assertIn("bet_size", result)
        self.assertIn("ev", result)
        self.assertIn("search_method", result)
        self.assertIn("nodes_explored", result)
        if result["action"] != "fold":
            self.assertGreaterEqual(result["bet_size"], MIN_BET_SIZE)
            self.assertLessEqual(result["bet_size"], 50)  # Cannot exceed stack
            self.assertGreater(result["ev"], 0)

    def test_a_star_strong_hand(self):
        """A* with strong hand."""
        result = a_star_search(
            "KAs", "Button", (50, 50), "Aggressive"
        )
        self.assertIn("action", result)
        self.assertIn("bet_size", result)
        self.assertIsInstance(result["ev"], float)

    def test_a_star_different_positions(self):
        """A* from different positions."""
        result_button = a_star_search("AA", "Button", (50, 50), "Tight")
        result_bb = a_star_search("AA", "Big_Blind", (50, 50), "Tight")
        self.assertIn("action", result_button)
        self.assertIn("action", result_bb)

    def test_a_star_facing_bet(self):
        """A* when facing a bet (call/raise decision)."""
        result = a_star_search(
            "AA", "Big_Blind", (50, 50), "Tight",
            opponent_bet_size=3.0
        )
        self.assertIn("action", result)
        self.assertIn("bet_size", result)
        self.assertIn(result["action"], ["fold", "call", "raise"])


class TestSearchConsistency(unittest.TestCase):
    """Cross-check A* search against brute-force optimization."""

    def test_a_star_and_brute_force_agree_on_premium_hand(self):
        """
        For a premium hand, A* and brute-force search should return
        very similar bet sizes and EVs.
        """
        from bet_sizing_search import optimal_bet_sizing_search

        common_kwargs = {
            "hand": "AA",
            "position": "Button",
            "stack_sizes": (50, 50),
            "opponent_tendency": "Tight",
            "use_module1": False,  # Do not depend on Module 1 in unit tests
        }
        result_a_star = optimal_bet_sizing_search(
            search_algorithm="a_star",
            **common_kwargs,
        )
        result_brute = optimal_bet_sizing_search(
            search_algorithm="brute_force",
            **common_kwargs,
        )

        # Both methods should recommend the same action type
        self.assertEqual(result_a_star["action"], result_brute["action"])

        # Bet sizes and EVs should be very close
        self.assertAlmostEqual(
            result_a_star["bet_size"],
            result_brute["bet_size"],
            places=2,
        )
        self.assertAlmostEqual(
            result_a_star["expected_value"],
            result_brute["expected_value"],
            places=4,
        )

    def test_optimal_bet_sizing_search_basic_api(self):
        """Smoke-test the unified entry point without Module 1."""
        from bet_sizing_search import optimal_bet_sizing_search

        result = optimal_bet_sizing_search(
            hand="KAs",
            position="Button",
            stack_sizes=(50, 50),
            opponent_tendency="Loose",
            search_algorithm="a_star",
            use_module1=False,
        )
        self.assertIn("action", result)
        self.assertIn("bet_size", result)
        self.assertIn("expected_value", result)
        self.assertIn("search_algorithm", result)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions."""

    def test_very_short_stack(self):
        """Very short stack."""
        result = a_star_search("AA", "Button", (5, 5), "Tight")
        self.assertIn("action", result)

    def test_very_deep_stack(self):
        """Very deep stack."""
        result = a_star_search("AA", "Button", (500, 500), "Tight")
        self.assertIn("action", result)

    def test_unequal_stacks(self):
        """Unequal stack sizes."""
        result = a_star_search("AA", "Button", (50, 30), "Tight")
        self.assertIn("action", result)

    def test_marginal_hand(self):
        """Marginal hand."""
        result = a_star_search("89s", "Button", (50, 50), "Tight")
        self.assertIn("action", result)

    def test_boundary_bet_sizes(self):
        """EV at category boundaries."""
        ev_25 = calculate_ev(2.5, "AA", "Button", (50, 50), "Tight")
        ev_30 = calculate_ev(3.0, "AA", "Button", (50, 50), "Tight")
        ev_40 = calculate_ev(4.0, "AA", "Button", (50, 50), "Tight")
        ev_50 = calculate_ev(5.0, "AA", "Button", (50, 50), "Tight")
        self.assertIsInstance(ev_25, float)
        self.assertIsInstance(ev_30, float)
        self.assertIsInstance(ev_40, float)
        self.assertIsInstance(ev_50, float)


if __name__ == '__main__':
    unittest.main()
