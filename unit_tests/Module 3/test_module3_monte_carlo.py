"""
Unit tests for Module 3: Monte Carlo Optimal Opening Actions.

These tests are intentionally lightweight and focus on:
- Shape and basic properties of the Monte Carlo API.
- Sanity checks that bet-size–dependent opponent behavior is wired up.
"""

import unittest
import sys
from pathlib import Path

# Add Module 3 directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "Module 3"))

from monte_carlo_simulator import (  # type: ignore
    _get_adjusted_opponent_probs,
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

