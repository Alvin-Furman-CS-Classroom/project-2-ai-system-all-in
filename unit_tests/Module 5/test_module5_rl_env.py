"""Tests for Module 5 training environment (full_game_engine)."""

import math
import random
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
M5 = ROOT / "Module 5"
for p in (ROOT, M5):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from action_mapping import DISCRETE_BUCKETS, legal_buckets, map_bucket_to_action
from full_game_engine.hu_hand import apply_action, legal_actions, new_hand
from rl_agent import RLPokerAgent
from rl_env import random_combined_stacks, run_episode
from state_encoder import encode_from_hand_state
from trainer import evaluate_bb_per_hand, train_self_play


class TestActionMapping(unittest.TestCase):
    def test_map_never_raises(self):
        rng = random.Random(0)
        for _ in range(30):
            s = new_hand([400, 400], rng=rng, button=rng.randint(0, 1))
            while s.phase not in {"hand_over"}:
                if s.phase not in {"preflop", "flop", "turn", "river"}:
                    break
                if not legal_actions(s):
                    break
                for b in DISCRETE_BUCKETS:
                    act = map_bucket_to_action(s, b)
                    self.assertIn("kind", act)
                a = map_bucket_to_action(s, rng.choice(DISCRETE_BUCKETS))
                apply_action(s, a)


class TestEncoder(unittest.TestCase):
    def test_encode_is_hashable(self):
        rng = random.Random(1)
        s = new_hand([200, 200], rng=rng, button=0)
        t = encode_from_hand_state(s, 0)
        self.assertIsInstance(t, tuple)
        {t: 1}  # hashable


class TestRandomCombinedStacks(unittest.TestCase):
    def test_sum_is_total_bb_in_chips(self):
        rng = random.Random(0)
        bb = 20
        for _ in range(50):
            s = random_combined_stacks(200, bb, rng, min_each_bb=5)
            self.assertEqual(s[0] + s[1], 200 * bb)
            self.assertGreaterEqual(s[0], 5 * bb)
            self.assertGreaterEqual(s[1], 5 * bb)


class TestLegalBuckets(unittest.TestCase):
    def test_legal_buckets_nonempty(self):
        rng = random.Random(2)
        s = new_hand([400, 400], rng=rng, button=0)
        lb = legal_buckets(s)
        self.assertTrue(len(lb) >= 1)
        self.assertTrue(len(lb) <= len(DISCRETE_BUCKETS))


class TestSaveLoad(unittest.TestCase):
    def test_save_load_roundtrip(self):
        a = RLPokerAgent(actions=list(DISCRETE_BUCKETS), epsilon=0.05)
        a.update_monte_carlo(("s",), "fold", 1.0)
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "policy.pkl"
            a.save(path, extra={"episodes_completed": 42, "final_button": 1})
            b = RLPokerAgent.load(path)
        self.assertEqual(b.epsilon, 0.05)
        self.assertEqual(b.q[("s",)]["fold"], a.q[("s",)]["fold"])
        self.assertEqual(b._training_extra.get("episodes_completed"), 42)
        self.assertEqual(b._training_extra.get("final_button"), 1)


class TestRunEpisodeRandomOpponent(unittest.TestCase):
    def test_random_legal_seat_only_records_rl_moves(self):
        rng = random.Random(3)

        def select(_state, _enc, _hero):
            return "check_call"

        res = run_episode(
            select,
            rng,
            [400, 400],
            button=0,
            random_legal_seat=1,
        )
        self.assertTrue(all(step.hero == 0 for step in res.steps))

    def test_train_with_random_legal_opponent_prob(self):
        rng = random.Random(11)
        agent = RLPokerAgent(actions=list(DISCRETE_BUCKETS), epsilon=0.0)
        train_self_play(
            agent,
            episodes=8,
            rng=rng,
            starting_bb_each=60,
            random_legal_opponent_prob=1.0,
        )
        self.assertGreater(len(agent.q), 0)


class TestTrainSelfPlayReturn(unittest.TestCase):
    def test_returns_seat_bb_and_button(self):
        rng = random.Random(0)
        agent = RLPokerAgent(actions=list(DISCRETE_BUCKETS), epsilon=0.0)
        seat0, btn = train_self_play(agent, episodes=3, rng=rng, starting_bb_each=80)
        self.assertEqual(len(seat0), 3)
        self.assertIn(btn, (0, 1))


class TestTrainingSmoke(unittest.TestCase):
    def test_train_and_eval_runs(self):
        rng = random.Random(7)
        agent = RLPokerAgent(actions=list(DISCRETE_BUCKETS), epsilon=0.3)
        train_self_play(agent, episodes=15, rng=rng, starting_bb_each=50)
        ev = evaluate_bb_per_hand(agent, episodes=10, rng=random.Random(8))
        self.assertTrue(
            math.isfinite(ev.mean_seat0)
            and math.isfinite(ev.mean_seat1)
            and math.isfinite(ev.mean_combined)
            and math.isfinite(ev.mean_seat_diff)
        )


if __name__ == "__main__":
    unittest.main()
