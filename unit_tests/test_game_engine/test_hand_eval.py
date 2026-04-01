"""Tests for 7-card evaluation and HU preflop engine."""

import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from game_engine.cards import Card
from game_engine.hand_eval import compare_at_showdown
from game_engine.hu_preflop import apply_action, new_hand, random_legal_action


class TestCompare(unittest.TestCase):
    def test_aa_beats_kk_on_blank_board(self):
        aa = (Card.from_str("As"), Card.from_str("Ah"))
        kk = (Card.from_str("Kd"), Card.from_str("Ks"))
        board = [Card.from_str(x) for x in ["2c", "3d", "7h", "9s", "Jc"]]
        self.assertEqual(compare_at_showdown(aa, kk, board), 1)

    def test_chop_same_hand(self):
        a = (Card.from_str("As"), Card.from_str("Ks"))
        b = (Card.from_str("Ah"), Card.from_str("Kh"))
        board = [Card.from_str(x) for x in ["Qd", "Jc", "Td", "2c", "3h"]]
        self.assertEqual(compare_at_showdown(a, b, board), 0)


class TestChipConservation(unittest.TestCase):
    def test_random_play(self):
        rng = random.Random(42)
        for t in range(200):
            s = [2000, 2000]
            h = new_hand(s, rng=rng, button=t % 2)
            total = sum(h.stacks) + h.pot
            while h.phase == "preflop":
                apply_action(h, random_legal_action(h, rng))
            self.assertEqual(sum(h.stacks) + h.pot, total)


class TestDecisionMetaHistory(unittest.TestCase):
    def test_apply_action_stores_llm_blob_when_provided(self):
        rng = random.Random(0)
        h = new_hand([200, 200], rng=rng, button=0, sb_chips=10, bb_chips=20)
        meta = {"reason": "test", "model": "stub", "street": "preflop"}
        apply_action(h, {"kind": "call"}, decision_meta=meta)
        last = [e for e in h.history if e.get("player") == 0][-1]
        self.assertIn("llm", last)
        self.assertEqual(last["llm"]["reason"], "test")


if __name__ == "__main__":
    unittest.main()
