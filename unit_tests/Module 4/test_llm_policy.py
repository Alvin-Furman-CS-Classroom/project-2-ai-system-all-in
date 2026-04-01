"""Tests for Module 4 LLM policy (Ollama mode, mocked network calls)."""

from __future__ import annotations

import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_M4 = ROOT / "Module 4"
if str(_M4) not in sys.path:
    sys.path.insert(0, str(_M4))

from game_engine.hu_preflop import apply_action, legal_actions, new_hand
from game_engine.mc_bot import hole_cards_to_mc_hand


class TestHandStateSnapshot(unittest.TestCase):
    def test_snapshot_keys(self):
        import llm_policy

        rng = random.Random(0)
        state = new_hand([2000, 2000], rng=rng, button=0)
        apply_action(state, {"kind": "call", "amount": state.to_call(0)})
        c0, c1 = state.hole_cards[1]
        hand = hole_cards_to_mc_hand(c0, c1)
        snap = llm_policy.hand_state_to_snapshot(state, 1, hand)
        self.assertIn("hero_hand", snap)
        self.assertIn("pot_bb", snap)
        self.assertEqual(snap["actor_seat"], 1)

    def test_full_game_snapshot_includes_street_board(self):
        import llm_policy
        from full_game_engine.hu_hand import new_hand as fg_new

        rng = random.Random(1)
        st = fg_new([2000, 2000], rng=rng, button=0)
        snap = llm_policy.hand_state_to_snapshot(st, st.actor, "AA")
        self.assertEqual(snap["street"], "preflop")
        self.assertEqual(snap["board"], [])


class TestParseLlmJsonBlob(unittest.TestCase):
    def test_plain_json(self):
        import llm_policy

        d = llm_policy._parse_llm_json_blob('{"option_index": 0, "reason": "x"}')
        self.assertEqual(d["option_index"], 0)

    def test_fenced_json(self):
        import llm_policy

        raw = '```json\n{"option_index": 1, "reason": "y"}\n```'
        d = llm_policy._parse_llm_json_blob(raw)
        self.assertEqual(d["option_index"], 1)

    def test_json_embedded_in_prose(self):
        import llm_policy

        raw = 'Here: {"option_index": 0, "reason": "fold"} done'
        d = llm_policy._parse_llm_json_blob(raw)
        self.assertEqual(d["option_index"], 0)

    def test_plain_text_option_index_fallback(self):
        import llm_policy

        raw = "option_index: 1\nreason: top pair blocker"
        d = llm_policy._parse_llm_json_blob(raw)
        self.assertEqual(d["option_index"], 1)
        self.assertIn("reason", d)


class TestChooseLegalIndexMocked(unittest.TestCase):
    def test_valid_index_returns_action(self):
        import llm_policy

        def ok_ollama(_user_text: str, timeout_s=None):
            return {"option_index": 1, "reason": "test"}

        orig = llm_policy._call_ollama
        llm_policy._call_ollama = ok_ollama
        try:
            rng = random.Random(0)
            idx, meta = llm_policy.choose_legal_index(
                {"hero_hand": "AKs"},
                [{"kind": "fold"}, {"kind": "check"}, {"kind": "raise_to", "total": 60}],
                rng=rng,
            )
            self.assertEqual(idx, 1)
            self.assertEqual(meta.get("provider"), "ollama")
            self.assertIn("reason", meta)
        finally:
            llm_policy._call_ollama = orig

    def test_one_based_index_normalized_when_in_range(self):
        """If the model returns 1..n (human numbering), map to 0..n-1."""
        import llm_policy

        def ok_ollama(_user_text: str, timeout_s=None):
            return {"option_index": 2, "reason": "second line"}

        orig = llm_policy._call_ollama
        llm_policy._call_ollama = ok_ollama
        try:
            idx, _ = llm_policy.choose_legal_index(
                {},
                [{"kind": "fold"}, {"kind": "call", "amount": 10}],
                rng=random.Random(0),
            )
            self.assertEqual(idx, 1)
        finally:
            llm_policy._call_ollama = orig

    def test_choose_preflop_action_returns_legal_dict(self):
        import llm_policy

        def fake_call(_user_text: str, timeout_s=None):
            return {"option_index": 0, "reason": "fold"}

        orig = llm_policy._call_ollama
        llm_policy._call_ollama = fake_call
        try:
            rng = random.Random(0)
            state = new_hand([2000, 2000], rng=rng, button=0)
            apply_action(state, {"kind": "call", "amount": state.to_call(0)})
            legal = legal_actions(state)
            c0, c1 = state.hole_cards[1]
            hand = hole_cards_to_mc_hand(c0, c1)
            act = llm_policy.choose_preflop_action(state, hand, legal, rng)
            self.assertEqual(act["kind"], legal[0]["kind"])
        finally:
            llm_policy._call_ollama = orig

    def test_error_when_ollama_fails(self):
        import llm_policy

        def fail_ollama(_user_text: str, timeout_s=None):
            raise RuntimeError("ollama down")

        orig_o = llm_policy._call_ollama
        llm_policy._call_ollama = fail_ollama
        try:
            with self.assertRaises(ValueError):
                llm_policy.choose_legal_index(
                    {"hero_hand": "AKs"},
                    [{"kind": "fold"}, {"kind": "check"}],
                    rng=random.Random(0),
                )
        finally:
            llm_policy._call_ollama = orig_o

    def test_default_reason_when_missing(self):
        import llm_policy

        def ollama_no_reason(_user_text: str, timeout_s=None):
            return {"option_index": 0}

        orig_o = llm_policy._call_ollama
        llm_policy._call_ollama = ollama_no_reason
        try:
            idx, meta = llm_policy.choose_legal_index(
                {"hero_hand": "AKs"},
                [{"kind": "fold"}, {"kind": "check"}],
                rng=random.Random(0),
            )
            self.assertEqual(idx, 0)
            self.assertEqual(meta.get("reason"), "No reason provided by model.")
        finally:
            llm_policy._call_ollama = orig_o


if __name__ == "__main__":
    unittest.main()
