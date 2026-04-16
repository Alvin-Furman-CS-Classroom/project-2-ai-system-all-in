"""Tests for full_game_engine HU hand engine (multi-street + all-in behavior)."""

import random
import unittest
from pathlib import Path

import project_paths

ROOT = Path(__file__).resolve().parent.parent.parent
project_paths.ensure_paths((ROOT,))

from full_game_engine.hu_hand import apply_action, legal_actions, new_hand


class TestStreetProgression(unittest.TestCase):
    def test_checkdown_deals_all_streets(self):
        rng = random.Random(123)
        h = new_hand([200, 200], rng=rng, button=0, sb_chips=10, bb_chips=20)
        total0 = sum(h.stacks) + h.pot

        # Preflop: BTN calls, BB checks -> advance to flop.
        apply_action(h, {"kind": "call"})
        apply_action(h, {"kind": "check"})
        self.assertEqual(h.phase, "flop")
        self.assertEqual(len(h.board), 3)

        # Flop: check/check -> turn
        apply_action(h, {"kind": "check"})
        apply_action(h, {"kind": "check"})
        self.assertEqual(h.phase, "turn")
        self.assertEqual(len(h.board), 4)

        # Turn: check/check -> river
        apply_action(h, {"kind": "check"})
        apply_action(h, {"kind": "check"})
        self.assertEqual(h.phase, "river")
        self.assertEqual(len(h.board), 5)

        # River: check/check -> showdown -> hand_over
        apply_action(h, {"kind": "check"})
        apply_action(h, {"kind": "check"})
        self.assertEqual(h.phase, "hand_over")
        self.assertEqual(len(h.board), 5)
        self.assertEqual(sum(h.stacks) + h.pot, total0)


class TestDecisionMetaHistory(unittest.TestCase):
    def test_apply_action_stores_llm_blob_when_provided(self):
        rng = random.Random(0)
        h = new_hand([200, 200], rng=rng, button=0, sb_chips=10, bb_chips=20)
        meta = {"reason": "equilibrium call", "street": "preflop"}
        apply_action(h, {"kind": "call"}, decision_meta=meta)
        player_events = [e for e in h.history if "player" in e]
        self.assertTrue(player_events)
        self.assertIn("llm", player_events[-1])
        self.assertEqual(player_events[-1]["llm"]["reason"], "equilibrium call")


class TestAllInRunout(unittest.TestCase):
    def test_short_all_in_call_returns_uncalled_and_runs_out(self):
        rng = random.Random(7)
        # Give BB a covering stack so BTN can be short all-in calling.
        h = new_hand([120, 300], rng=rng, button=0, sb_chips=10, bb_chips=20)
        total0 = sum(h.stacks) + h.pot

        # BTN calls to 20.
        apply_action(h, {"kind": "call"})
        # BB makes a large raise, bigger than BTN can fully call.
        apply_action(h, {"kind": "raise_to", "total": 200})

        # BTN should have a legal all-in call for less than full amount.
        acts = legal_actions(h)
        call_actions = [a for a in acts if a["kind"] == "call"]
        self.assertEqual(len(call_actions), 1)
        self.assertLess(call_actions[0]["amount"], h.to_call(h.actor))

        apply_action(h, {"kind": "call"})

        # Hand should auto-runout and resolve.
        self.assertEqual(h.phase, "hand_over")
        self.assertEqual(len(h.board), 5)
        self.assertEqual(h.pot, 0)
        self.assertEqual(sum(h.stacks) + h.pot, total0)

        # Uncalled return event should exist (covering player got excess back).
        events = [e for e in h.history if e.get("event") == "uncalled_return"]
        self.assertTrue(events)


if __name__ == "__main__":
    unittest.main()

