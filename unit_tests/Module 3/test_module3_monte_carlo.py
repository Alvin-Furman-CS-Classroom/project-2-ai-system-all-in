"""
Unit tests for Module 3: Monte Carlo Optimal Opening Actions.

These tests are intentionally lightweight and focus on:
- Shape and basic properties of the Monte Carlo API.
- Sanity checks that bet-size–dependent opponent behavior is wired up.
"""

import unittest
import sys
import random
from pathlib import Path

# Project root (for full_game_engine) and Module 3
_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "Module 3"))

from full_game_engine.cards import Card

from monte_carlo_simulator import (  # type: ignore
    _get_adjusted_opponent_probs,
    monte_carlo_equity_vs_conditioned_range,
    run_simulation,
    run_simulation_for_strategy,
)
from bet_sizing_optimizer import (  # type: ignore
    optimize_opening_actions,
    get_opening_strategy_for_module4,
)
from strategy_evaluator import evaluate_strategy  # type: ignore


class TestOpponentProbabilitiesMonteCarlo(unittest.TestCase):
    """Test that Monte Carlo opponent probabilities adjust with bet size."""

    def test_adjusted_probabilities_monotonic_with_bet_size(self):
        """
        Small bets should induce fewer folds and more calls than large bets
        for the same opponent tendency.
        """
        small = _get_adjusted_opponent_probs("Tight", 2.0)
        large = _get_adjusted_opponent_probs("Tight", 6.0)

        # Sanity: probabilities sum to ~1
        self.assertAlmostEqual(
            small["fold"] + small["call"] + small["raise"], 1.0, places=5
        )
        self.assertAlmostEqual(
            large["fold"] + large["call"] + large["raise"], 1.0, places=5
        )

        # Small bet: fewer folds, more calls than large bet
        self.assertLess(small["fold"], large["fold"])
        self.assertGreater(small["call"], large["call"])


class TestRunSimulation(unittest.TestCase):
    """Smoke tests for single-hand Monte Carlo simulation."""

    def test_run_simulation_basic_open(self):
        """run_simulation returns numeric value and CI for a standard open."""
        result = run_simulation(
            hand="AA",
            action="open",
            bet_size=3.0,
            position="Button",
            stack_sizes=(50, 50),
            opponent_tendency="Tight",
            num_trials=200,
            pot_size=1.5,
            seed=123,
        )
        self.assertIn("value_estimate", result)
        self.assertIn("std", result)
        self.assertIn("confidence_interval", result)
        self.assertIn("num_trials", result)
        self.assertEqual(result["num_trials"], 200)
        self.assertIsInstance(result["value_estimate"], float)

    def test_run_simulation_fold_zero(self):
        """Folding should always have value 0 in this model."""
        result = run_simulation(
            hand="AA",
            action="fold",
            bet_size=0.0,
            position="Button",
            stack_sizes=(50, 50),
            opponent_tendency="Tight",
            num_trials=100,
            pot_size=1.5,
            seed=42,
        )
        self.assertAlmostEqual(result["value_estimate"], 0.0, places=6)

    def test_run_simulation_postflop_board_affects_value(self):
        """With hero hole + board, EV uses board-aware equity (not preflop table only)."""
        hole = (Card.from_str("7d"), Card.from_str("2c"))
        wet = [Card.from_str("9h"), Card.from_str("Th"), Card.from_str("Jh")]
        dry = [Card.from_str("2s"), Card.from_str("3d"), Card.from_str("8c")]
        base = dict(
            hand="72o",
            action="open",
            bet_size=2.0,
            position="Button",
            stack_sizes=(50, 50),
            opponent_tendency="Unknown",
            num_trials=400,
            pot_size=4.0,
            seed=99,
        )
        r_wet = run_simulation(**base, hero_hole=hole, board=wet)
        r_dry = run_simulation(**base, hero_hole=hole, board=dry)
        self.assertGreater(
            abs(r_wet["value_estimate"] - r_dry["value_estimate"]),
            1e-6,
            "board-aware equity should change EV vs different board textures",
        )

    def test_conditioned_raise_range_stronger_than_call(self):
        """Raise continuing range should leave weak heroes worse off than call range."""
        hole = (Card.from_str("7d"), Card.from_str("2c"))
        board = [Card.from_str("Ah"), Card.from_str("Kh"), Card.from_str("Qh")]
        eq_call = monte_carlo_equity_vs_conditioned_range(
            hole,
            board,
            "call",
            "Unknown",
            3.0,
            random.Random(7),
            num_samples=600,
        )
        eq_raise = monte_carlo_equity_vs_conditioned_range(
            hole,
            board,
            "raise",
            "Unknown",
            3.0,
            random.Random(7),
            num_samples=600,
        )
        self.assertLess(eq_raise, eq_call)

    def test_conditioned_equity_reproducible_with_seed(self):
        """Same seed and sample count yields identical conditioned equity."""
        hole = (Card.from_str("Td"), Card.from_str("9d"))
        board = [Card.from_str("Jc"), Card.from_str("8h"), Card.from_str("2s")]
        a = monte_carlo_equity_vs_conditioned_range(
            hole,
            board,
            "call",
            "Tight",
            2.5,
            random.Random(404),
            num_samples=250,
        )
        b = monte_carlo_equity_vs_conditioned_range(
            hole,
            board,
            "call",
            "Tight",
            2.5,
            random.Random(404),
            num_samples=250,
        )
        self.assertEqual(a, b)


class TestStrategySimulation(unittest.TestCase):
    """Tests for strategy-level Monte Carlo evaluation and optimization."""

    def test_run_simulation_for_strategy_shape(self):
        """Strategy simulation returns expected keys and per-hand results."""
        strategy = {"AA": 3.0, "72o": 0.0}  # open AA, fold 72o
        result = run_simulation_for_strategy(
            strategy=strategy,
            position="Button",
            stack_sizes=(50, 50),
            opponent_tendency="Tight",
            num_trials_per_hand=100,
            seed=1,
        )
        self.assertIn("expected_value", result)
        self.assertIn("confidence_interval", result)
        self.assertIn("per_hand_results", result)
        self.assertEqual(result["num_hands"], 2)
        self.assertIn("AA", result["per_hand_results"])
        self.assertIn("72o", result["per_hand_results"])

    def test_optimize_opening_actions_basic(self):
        """optimize_opening_actions returns a reasonable strategy object."""
        result = optimize_opening_actions(
            position="Button",
            stack_sizes=(50, 50),
            opponent_tendency="Tight",
            hands=["AA", "72o"],
            candidate_bet_sizes=[2.0, 3.0],
            num_simulations=100,
            seed=7,
        )
        self.assertIn("optimized_strategy", result)
        self.assertIn("expected_value", result)
        self.assertIn("confidence_interval", result)
        self.assertIn("hand_recommendations", result)

        strategy = result["optimized_strategy"]
        self.assertIn("AA", strategy)
        self.assertIn("72o", strategy)

    def test_tight_opponent_does_not_prefer_bigger_bet_for_72o(self):
        """
        Against a Tight opponent, 72o should not strictly prefer a larger bet size
        than AA when both consider the same candidate sizes.

        This is a sanity check on the interaction between fold equity and hand strength.
        """
        result = optimize_opening_actions(
            position="Button",
            stack_sizes=(50, 50),
            opponent_tendency="Tight",
            hands=["AA", "72o"],
            candidate_bet_sizes=[2.0, 3.0, 4.0, 5.0],
            num_simulations=400,
            seed=123,
        )
        strategy = result["optimized_strategy"]
        bet_aa = strategy.get("AA", 0.0)
        bet_72o = strategy.get("72o", 0.0)

        # We allow equality, but 72o should not choose a strictly larger sizing than AA.
        self.assertLessEqual(bet_72o, bet_aa + 1e-6)

    def test_evaluate_strategy_smoke(self):
        """evaluate_strategy works on a small concrete strategy."""
        strategy = {"AA": 3.0, "KK": 3.0, "72o": 0.0}
        result = evaluate_strategy(
            strategy=strategy,
            position="Button",
            stack_sizes=(50, 50),
            opponent_tendency="Loose",
            num_trials=100,
            seed=99,
        )
        self.assertIn("expected_value", result)
        self.assertIn("confidence_interval", result)
        self.assertIn("per_hand_ev", result)
        self.assertEqual(set(result["per_hand_ev"].keys()), set(strategy.keys()))

    def test_get_opening_strategy_for_module4_smoke(self):
        """Module 4 helper returns same structure as optimize_opening_actions."""
        result = get_opening_strategy_for_module4(
            position="Button",
            stack_sizes=(50, 50),
            opponent_tendency="Unknown",
            num_simulations=50,
            seed=5,
        )
        self.assertIn("optimized_strategy", result)
        self.assertIn("expected_value", result)
        self.assertIn("confidence_interval", result)


if __name__ == "__main__":
    unittest.main()

