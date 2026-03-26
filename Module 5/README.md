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

## Action Space (Discrete Buckets)

The agent uses discrete action buckets in big-blind / pot-relative units:

- `fold`
- `check_call`
- `bet_raise_0.5_pot`
- `bet_raise_0.75_pot`
- `bet_raise_1.0_pot`
- `bet_raise_1.5_pot`
- `all_in`

Pre-flop open recommendations are mapped from these buckets to legal engine actions.
When needed, opening sizes can be clamped to standard legal ranges (e.g. 2.0x to 5.0x BB).

## State Representation

State includes the same style of context used in earlier modules, plus board data:

- Hand information (hero hole cards / encoded hand class)
- Position (Button / Big Blind or IP/OOP)
- Stack sizes / effective stack (in BB, bucketed)
- Pot size (in BB, bucketed)
- To-call amount (in BB, bucketed)
- Opponent tendency or online opponent-profile features (if available)
- Betting context features (last aggression, action depth)
- **Board features** (street, board texture buckets, paired/flush/straight potential)

Implementation target: hashable tuple state for tabular Q-learning.

## Reward Design

- **Reward type:** Terminal reward only
- **Unit:** Big blinds (BB)
- **Definition:** Net BB won/lost at hand end assigned to trajectory (no intermediate shaping initially)

## Training Data

- **Source:** Pure self-play to start
- Episodes generated via the game engine environment and converted into transitions:
  `(state, action, reward, next_state, done)`

## Learning Algorithm

- **Algorithm:** Tabular Q-learning
- Update:
  `Q(s,a) <- Q(s,a) + alpha * (r + gamma * max_a' Q(s',a') - Q(s,a))`

## Exploration Policy (Recommended)

Use epsilon-greedy with decay:

- Start `epsilon = 0.20`
- End `epsilon = 0.02`
- Decay linearly over first 70% of training episodes
- Keep floor at `0.02` for continued exploration

Suggested initial hyperparameters:

- `alpha = 0.10`
- `gamma = 0.95`
- deterministic eval mode uses `epsilon = 0.0`

## Outputs

- Learned policy (state -> action)
- Q-values (tabular or approximation)
- Exploitation recommendations against opponent tendencies
- **Primary success metric:** BB/hand

## Files

- `rl_agent.py` – Core Q-learning style agent and action selection logic.
- `state_encoder.py` – Converts game/hand context into RL state features.
- `trainer.py` – Training loop utilities over episodes/transitions.
- `demo_module5.py` – Demo script showing train + inference flow.

## Evaluation Protocol

- Report **BB/hand** as the primary metric.
- Evaluate in separate runs (no exploration, `epsilon=0`) against:
  - Self-play checkpoints
  - Other fixed bots in the system (as available)
- Use large enough hand counts for stable BB/hand estimates.

## Integration Target

This module should plug into `game_engine` as a selectable bot policy, similar to
existing bot routing (`random`, `m12`, `m3`), with a new RL-backed option.

Expected integration behavior:

- Accept current `HandState` from `game_engine`
- Encode to RL state via `state_encoder.py`
- Select legal action bucket via `rl_agent.py`
- Map bucket to a legal engine action (`fold/call/check/raise_to/all-in`)
- Return action dict compatible with `game_engine.hu_preflop.apply_action`

## Running the demo

```bash
python3 "Module 5/demo_module5.py"
```

