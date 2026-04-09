# Module 3: Monte Carlo Optimal Opening Actions

**Topics:** Monte Carlo Methods, Optimization

## Purpose

This module uses **Monte Carlo simulation only** to compute optimal opening actions (fold or open to X BB). It does not rely on Module 2: no heuristics or closed-form expected value formulas are used. Outcomes are simulated (e.g., opponent actions, hand runouts), and the action that maximizes simulated value is chosen. Results include expected value and confidence intervals for use by Module 4 and later modules.

## Inputs

- Position (Button / Big Blind)
- Stack sizes (tuple)
- Opponent tendency category
- Optional: list of hands (or hand range) to evaluate; if omitted, a default set can be used

**Independence:** This module does **not** use Module 1 or Module 2. It is suitable as a standalone Monte Carlo agent that can compete against the rule-based + search agent (Modules 1–2) on equal footing—same inputs are game state and tendency, not another module’s output.

## Outputs

- Optimal opening action strategy (hand → fold or open to X BB), derived purely from Monte Carlo simulation
- Expected value of the strategy
- Confidence intervals from simulation
- Optional: list of hands and recommended opening actions

## Files

- `monte_carlo_simulator.py` – Core simulation: run trials (simulate outcomes), estimate value and variance/CI. No Module 2 or EV formulas.
- `strategy_evaluator.py` – Evaluate a candidate strategy (hand → bet size) via Monte Carlo.
- `bet_sizing_optimizer.py` – Find optimal opening actions by evaluating candidates via Monte Carlo (no Module 2 input).
- `demo_module3.py` – Demo script.

## Full Web App Integration

Module 3 is available in the full-hand web app via bot id `m3`.

- Routing: `full_game_engine/bot_agents.py`
- Action adapter: `full_game_engine/mc_bot.py`
- UI selector: `full_game_web_app/templates/index.html`

### Behavior note (all streets)

`m3` uses the current Monte Carlo adapter on preflop and postflop decisions.
Postflop decisions are approximation-based through the same action-to-simulation mapping,
so they are intended for practical gameplay integration rather than exact game-tree solving.

## Running the demo

From project root:

```bash
python3 "Module 3/demo_module3.py"
```

## Prerequisites

- Course content on Monte Carlo methods and optimization.
