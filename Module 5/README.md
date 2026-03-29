# Module 5: Adaptive Opponent Exploitation (Reinforcement Learning)

**Topics:** Reinforcement Learning (MDP, Policy, Value Functions, Q-Learning)

## Purpose

This module implements an RL-based poker agent that learns from gameplay outcomes and
adapts to opponent behavior over time. It focuses on policy learning from interaction
data rather than static rules.

## Scope

- **Game scope:** Entire hand (pre-flop + post-flop)
- **Format:** Heads-up only
- **Initial training mode:** Pure self-play
- **Training environment:** `full_game_engine` (see `rl_env.py`). Training does **not** depend on the web app.

## Action Space (Discrete Buckets)

The agent uses discrete action buckets; raises are interpreted in **pot-relative** terms and mapped to the closest legal `raise_to` total the engine allows:

- `fold`
- `check_call` (check if no bet; otherwise call)
- `bet_raise_0.5_pot`
- `bet_raise_0.75_pot`
- `bet_raise_1.0_pot`
- `bet_raise_1.5_pot`
- `all_in` (largest legal raise up to full stack, or call/check if raise is impossible)

Implementation: `action_mapping.py` (`DISCRETE_BUCKETS`, `map_bucket_to_action`, `legal_buckets` for exploration masking).

## State Representation

States are encoded from the **current actor’s** perspective (hero-centric self-play):

- Hole cards (coarse buckets: pair bands vs non-pair high/low/suited)
- Street (`preflop` … `river`)
- Position (button vs big blind)
- Hero and villain stack sizes (BB, bucketed)
- Pot and to-call (BB, bucketed)
- Board: card count plus coarse flags (paired board, monotone / flush potential)

Implementation: `state_encoder.py` (`encode_from_hand_state`). Output is a **hashable tuple** for tabular Q-learning. Optional dict-based `encode_state` remains for offline tests or logs.

## Reward Design

- **Unit:** Big blinds (BB)
- **Default training (`use_monte_carlo=True`):** every-visit **Monte Carlo** toward hand return: for each decision by seat *p*, the target is *G* = net BB change for seat *p* from hand start to hand end (same *G* for every step *p* took that hand). This avoids attributing the whole outcome to only the last action.
- **Optional TD (`use_monte_carlo=False`):** one-step Q-learning with `r = 0` on non-terminal steps and full-hand net BB on the **last** transition only (coarser credit; kept for comparison).

## Training Data

- **Source:** Pure self-play (both seats share the same policy).
- `run_episode` in `rl_env.py` records `StepRecord` rows `(encoded state, bucket, hero)`; `trainer.train_self_play` applies updates.

## Learning Algorithm

- **Monte Carlo (default):** `Q(s,a) <- Q(s,a) + alpha * (G - Q(s,a))` with *G* = seat’s net BB for the hand (`RLPokerAgent.update_monte_carlo`).
- **TD (optional):** tabular Q-learning with bootstrap (`RLPokerAgent.update`).
- Offline batch TD: `trainer.train_from_transitions` (optional).

## Exploration Policy (Recommended)

Epsilon-greedy with decay (implemented in `trainer.train_self_play`):

- Start `epsilon = 0.20`
- End `epsilon = 0.02`
- Decay linearly over the **first 70%** of training episodes; floor `0.02` thereafter
- **Masked exploration (`use_masked_exploration=True`, default):** random exploration is uniform over `legal_buckets(state)`—one representative bucket per distinct mapped engine action—so duplicate buckets are not over-sampled.
- Evaluation / reporting: `epsilon = 0.0` (see `evaluate_bb_per_hand`)

Suggested initial hyperparameters:

- `alpha = 0.10`
- `gamma = 0.95`

## Outputs

- Learned Q-table / greedy policy over discrete buckets
- **BB/hand reporting:** `evaluate_bb_per_hand` returns per-seat means plus **`mean_seat_diff`** = `mean_seat0 - mean_seat1`.

### Why `mean_combined` is not “zero-sum = 0”

Stack changes are measured **after blinds are posted**. The pot starts in the middle, not in either stack, so for each hand **seat0_BB + seat1_BB ≈ initial pot in BB** (typically ~1.5 BB), not 0. Therefore **`(mean_seat0 + mean_seat1) / 2`** tracks roughly **half of that** and should **not** be expected to converge to 0.

For **symmetric** self-play with alternating buttons, **`mean_seat_diff`** should trend toward **0** (neither seat has an advantage). Use **one seat’s** mean (e.g. `mean_seat0`) if you want a single “hero BB/hand” number, understanding it is relative to that seat’s role mix over the run.

## Files

| File | Role |
|------|------|
| `rl_agent.py` | `RLPokerAgent`: TD update, MC update, `select_action`, `select_action_masked` |
| `state_encoder.py` | `encode_from_hand_state(HandState, hero)` → hashable tuple |
| `action_mapping.py` | Bucket → legal `apply_action` dict for `full_game_engine` |
| `rl_env.py` | `run_episode`, `new_starting_stacks`, `random_combined_stacks` — self-play on `full_game_engine` |
| `trainer.py` | `train_self_play`, `evaluate_bb_per_hand`, `train_from_transitions` |
| `demo_module5.py` | Example train + greedy eval |
| `train_module5.py` | CLI: long runs, `--save-every`, `--resume`, checkpoint path |

## Long training (`train_module5.py`)

```bash
python3 "Module 5/train_module5.py" --episodes 10000 --save-every 500 --checkpoint "Module 5/checkpoints/policy.pkl"
python3 "Module 5/train_module5.py" --episodes 2000 --resume --checkpoint "Module 5/checkpoints/policy.pkl"
```

- **`--save-every N`:** writes the checkpoint every `N` episodes (and **Ctrl+C** saves once).
- **`--resume`:** loads the pickle (if present) and continues with stored **`episodes_completed`** and **dealer `final_button`**, and keeps the epsilon schedule indexed by **`--epsilon-schedule`** (default `10000`).
- **`--checkpoint`:** path to the policy pickle.

**Starting stacks (default):** each hand samples a **random split** of **`--combined-bb-total`** (default **200 BB**) between the two players, with at least **`--min-stack-bb`** (default **5 BB**) each so both can post blinds. Total chips are always `combined_bb_total × bb_chips`. Use **`--no-random-stacks`** for the old behavior (equal **`--starting-bb-each`** per player).

## Evaluation Protocol

- Report **BB/hand** over enough hands to stabilize the mean.
- Prefer **`mean_seat_diff` ≈ 0** as a symmetry check; do **not** use **`mean_combined`** as a zero-sum check (see above).
- Use **no exploration** (`epsilon = 0`) when measuring policy strength.
- Later: compare against fixed bots (random, Module 1–3 agents) when wired through the engine.

## Integration Target

**Training:** stays in Python scripts using `full_game_engine` only (no Flask).

**Future play / UI:** add an RL-backed bot alongside existing routing (same pattern as other agents):

- Read live `HandState` from **`full_game_engine`** (not the legacy pre-flop-only `game_engine` if you need post-flop).
- `encode_from_hand_state(state, state.actor)`
- `agent.select_action_masked(enc, legal_buckets(state))` (or `select_action` if you do not mask)
- `map_bucket_to_action(state, bucket)` → dict for `full_game_engine.hu_hand.apply_action`

## Saving and loading a trained policy

Training can run as long as you want (hours overnight, many episodes). **Inference is cheap**: only a Q-table lookup and `legal_buckets` mapping—no simulation.

After training, persist the agent and reload anytime:

```python
from pathlib import Path
from rl_agent import RLPokerAgent

agent = RLPokerAgent.load(Path("path/to/policy.pkl"))
agent.epsilon = 0.0  # greedy at play time
# ... encode state → select_action_masked → map_bucket_to_action ...
```

Save with `agent.save(Path("path/to/policy.pkl"))`. The file is **pickle** (tuple state keys); only load files you trust.

## Running the demo

```bash
python3 "Module 5/demo_module5.py"
```

## Tests

```bash
python3 -m unittest -q "unit_tests/Module 5/test_module5_rl_env.py"
```
