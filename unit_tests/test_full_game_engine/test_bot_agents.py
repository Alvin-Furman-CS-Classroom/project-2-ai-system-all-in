"""Integration tests for full_game_engine bot agent routing."""

import random
import unittest
from pathlib import Path

import project_paths

ROOT = Path(__file__).resolve().parent.parent.parent
project_paths.ensure_paths((ROOT,))

from full_game_engine.bot_agents import normalize_agent, pick_bot_action
from full_game_engine.hu_hand import apply_action, legal_actions, new_hand


class TestNormalizeAgent(unittest.TestCase):
    def test_accepts_m2(self):
        self.assertEqual(normalize_agent("m2"), "m2")

    def test_accepts_m3(self):
        self.assertEqual(normalize_agent("m3"), "m3")


class TestModule2BotActions(unittest.TestCase):
    def test_m2_returns_legal_action_preflop(self):
        rng = random.Random(2)
        h = new_hand([400, 400], rng=rng, button=0, sb_chips=10, bb_chips=20)
        act, _meta = pick_bot_action("m2", h, rng)
        self.assertIn(act, legal_actions(h))

    def test_m2_can_act_on_flop(self):
        rng = random.Random(3)
        h = new_hand([400, 400], rng=rng, button=0, sb_chips=10, bb_chips=20)
        # Advance to flop with legal preflop line.
        apply_action(h, {"kind": "call"})
        apply_action(h, {"kind": "check"})
        self.assertEqual(h.phase, "flop")
        act, _meta = pick_bot_action("m2", h, rng)
        self.assertIn(act, legal_actions(h))


class TestModule3BotActions(unittest.TestCase):
    def test_m3_returns_legal_action_preflop(self):
        rng = random.Random(10)
        h = new_hand([400, 400], rng=rng, button=0, sb_chips=10, bb_chips=20)
        act, _meta = pick_bot_action("m3", h, rng)
        self.assertIn(act, legal_actions(h))

    def test_m3_can_act_on_flop(self):
        rng = random.Random(11)
        h = new_hand([400, 400], rng=rng, button=0, sb_chips=10, bb_chips=20)
        apply_action(h, {"kind": "call"})
        apply_action(h, {"kind": "check"})
        self.assertEqual(h.phase, "flop")
        act, _meta = pick_bot_action("m3", h, rng)
        self.assertIn(act, legal_actions(h))

    def test_m3_can_act_on_turn(self):
        rng = random.Random(12)
        h = new_hand([400, 400], rng=rng, button=0, sb_chips=10, bb_chips=20)
        # Reach turn by checkdown.
        apply_action(h, {"kind": "call"})
        apply_action(h, {"kind": "check"})
        apply_action(h, {"kind": "check"})
        apply_action(h, {"kind": "check"})
        self.assertEqual(h.phase, "turn")
        act, _meta = pick_bot_action("m3", h, rng)
        self.assertIn(act, legal_actions(h))

    def test_m3_can_act_on_river(self):
        rng = random.Random(13)
        h = new_hand([400, 400], rng=rng, button=0, sb_chips=10, bb_chips=20)
        # Reach river by checkdown.
        apply_action(h, {"kind": "call"})
        apply_action(h, {"kind": "check"})
        apply_action(h, {"kind": "check"})
        apply_action(h, {"kind": "check"})
        apply_action(h, {"kind": "check"})
        apply_action(h, {"kind": "check"})
        self.assertEqual(h.phase, "river")
        act, _meta = pick_bot_action("m3", h, rng)
        self.assertIn(act, legal_actions(h))


if __name__ == "__main__":
    unittest.main()

