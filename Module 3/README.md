# Module 3: Monte Carlo Optimal Opening Actions

**Topics:** Monte Carlo Methods, Optimization

## Purpose

This module uses **Monte Carlo simulation only** to compute optimal opening actions (fold or open to X BB). It does not rely on Module 2: no heuristics or closed-form expected value formulas are used. Outcomes are simulated (e.g., opponent actions, hand runouts), and the action that maximizes simulated value is chosen. Results include expected value and confidence intervals for use by Module 4 and later modules.

## Inputs

- Position (Button / Big Blind)
- Stack sizes (tuple)
- Opponent tendency category
- Optional: knowledge base or playability from Module 1 (for filtering which hands to consider)
- Optional: list of hands (or hand range) to evaluate; if omitted, a default set can be used

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

## Running the demo

From project root:

```bash
python3 "Module 3/demo_module3.py"
```

## Prerequisites

- Course content on Monte Carlo methods and optimization.
- Module 1 is optional (for playability filtering only).
