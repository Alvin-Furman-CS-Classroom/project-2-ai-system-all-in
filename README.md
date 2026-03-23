# Heads-Up Pre-Flop Poker: Comparative Analysis of AI Agent Strategies

## Overview

This system provides a comprehensive platform for playing heads-up (two-player) Texas Hold'em pre-flop poker against AI agents, each implementing different AI techniques. The system integrates multiple AI paradigms to create four distinct agents: a rule-based agent using propositional logic and A* search; a Monte Carlo simulation agent; a game theory optimal (GTO) agent using Nash equilibrium; and an adaptive learning agent using reinforcement learning. Users can compete against any agent, and the system enables agent-versus-agent competitions to quantitatively compare the effectiveness of different AI approaches.

Poker is an ideal domain for exploring AI concepts because it combines incomplete information, strategic decision-making, and optimization challenges. The pre-flop phase provides a manageable scope while still requiring sophisticated analysis. By implementing each AI technique as a playable agent and enabling direct comparison, this system demonstrates how different AI paradigms perform in practice, revealing trade-offs between speed and accuracy, exploitation and unexploitability, and rule-based versus learning-based approaches. This comparative analysis makes the system both educationally valuable and practically useful for understanding AI strategy optimization.

### Agents

- **Agent 1 – Rule-Based + Search**: Uses Module 1 (Propositional Logic) to determine playability and Module 2 (A* Search) to find optimal bet sizes.
- **Agent 2 – Monte Carlo**: Uses Module 3 to compute optimal opening actions via Monte Carlo simulation (no heuristics or closed-form EV).
- **Agent 3 – GTO (Nash Equilibrium)**: Uses Module 4 to follow pre-flop Nash equilibrium strategies.
- **Agent 4 – Adaptive Learning**: Uses Module 5 (Reinforcement Learning) to learn and exploit opponent tendencies over time.

## Team

- Sean Rowland
- Hayes Brown

## Proposal

Link to approved Project 1 proposal: [Project 1 Proposal](https://github.com/Alvin-Furman-CS-Classroom/project-1-proposal-SeanRowland7)


## Module Plan

Your system must include 5-6 modules. Fill in the table below as you plan each module.

| Module | Topic(s) | Inputs | Outputs | Depends On | Checkpoint |
| ------ | -------- | ------ | ------- | ---------- | ---------- |
| 1 | Propositional Logic (Knowledge Bases, Inference Methods, Chaining, CNF) | Starting hand, position (Button/Big Blind), stack size (big blinds), opponent tendency category | Knowledge base of propositional logic rules in CNF format, playable decision | None | Wednesday, Feb 11 |
| 2 | Informed Search (A*, IDA*, Beam Search), Optimization | Starting hand, position, stack sizes (tuple), opponent tendency, Module 1 knowledge base | Optimal bet size (multiple of big blind), action recommendation (fold/call/raise), expected value | Module 1 | Thursday, Feb 26 |
| 3 | Monte Carlo Methods, Optimization | Position (Button/Big Blind), stack sizes (tuple), opponent tendency category | Optimal opening action strategy (fold or open to X BB) with expected value and confidence intervals | None | Thursday, March 19 |
| 4 | Game Theory (Minimax, Nash Equilibrium, Mixed Strategies) | Position, stack sizes, Modules 2-3 optimized strategies, Module 1 knowledge base | Deviation metrics, exploitability analysis, equilibrium reference data | Modules 1, 2, 3 | Thursday, April 2 |
| 5 | Reinforcement Learning (MDP, Policy, Value Functions, Q-Learning) | Historical game data, opponent tendency, Module 4 equilibrium data, Module 3 opening ranges | Learned policy (Q-values), exploitation strategy recommendations | Modules 1, 3, 4 | Thursday, April 16 |

## Repository Layout

```
your-repo/
├── Module 1/                         # Module 1 source code (Propositional Logic)
├── unit_tests/                      # unit tests (parallel structure to modules)
│   └── Module 1/                    # Module 1 unit tests
├── docs/                            # documentation files
├── .claude/skills/code-review/SKILL.md  # rubric-based agent review
├── AGENTS.md                        # instructions for your LLM agent
└── README.md                        # system overview and checkpoints
```

## Setup

Modules 1-3 are implemented and ready to use.

Dependencies:
- Python 3.9+ recommended
- Install project dependencies: `pip install -r requirements.txt`

Setup steps:
1. Clone the repository
2. Ensure Python 3.7+ is installed
3. Install dependencies: `pip install -r requirements.txt`

Environment variables:
- None required

## Running

### Module 1: Propositional Logic Hand Decider

```python
import sys
sys.path.insert(0, 'Module 1')
from propositional_logic import propositional_logic_hand_decider

# Example usage
result = propositional_logic_hand_decider(
    hand="AA",
    position="Button",
    stack_size=50,
    opponent_tendency="Tight"
)

print(f"Playable: {result['playable']}")
print(f"Reason: {result['reason']}")
```

Commands for running modules:
- Module 1: Use Python import as shown above, or run interactively
- Module 2: `python3 "Module 2/demo_module2.py"`
- Module 3: `python3 "Module 3/demo_module3.py"`
- **Preflop + showdown web demo** (human vs random bot): `pip install -r requirements.txt` then `python3 -m web_app.server` — open http://127.0.0.1:5000/ — your move returns immediately; the bot’s “thinking” delay is **client-side** in `web_app/templates/index.html` (`BOT_THINK_MIN_MS` / `BOT_THINK_MAX_MS`).
- Module 4: `[command to be added]`
- Module 5: `[command to be added]`

## Testing

**Unit Tests** (`unit_tests/`): Mirror the structure of module directories. Each module has corresponding unit tests.

Test commands:
- Run Module 1 unit tests: `python3 -m unittest "unit_tests/Module 1/test_propositional_logic.py" -v`
- Run Module 2 unit tests: `python3 -m unittest "unit_tests/Module 2/test_bet_sizing_search.py" -v`
- Run Module 3 unit tests: `python3 -m unittest "unit_tests/Module 3/test_module3_monte_carlo.py" -v`
- Run all unit tests: `python3 -m unittest discover unit_tests -v`

Test data:
- Module 1 tests cover: all hand types, positions, opponent types, stack sizes, edge cases, and backward chaining scenarios
- 49 unit tests covering all functionality

## Checkpoint Log

| Checkpoint | Date | Modules Included | Status | Evidence |
| ---------- | ---- | ---------------- | ------ | -------- |
| 1 | Wednesday, Feb 11 | Module 1 (Propositional Logic) | ✅ Complete | Implementation: `Module 1/propositional_logic.py`, Tests: `unit_tests/Module 1/test_propositional_logic.py` (49 tests), Reports: `checkpoint_1_elegance_report.md`, `checkpoint_1_module_report.md` |
| 2 | Thursday, Feb 26 | Modules 1-2 (Propositional Logic, Informed Search) | ✅ Complete | Module 2 implementation: `Module 2/bet_sizing_search.py`, `Module 2/ev_calculator.py`, `Module 2/heuristic.py`, `Module 2/bet_size_discretization.py`; Demo: `Module 2/demo_module2.py`; Unit tests: `unit_tests/Module 2/test_bet_sizing_search.py`; Reports: `Module 2/checkpoint_2/checkpoint_2_module_report.md`, `Module 2/checkpoint_2/checkpoint_2_elegance_report.md` |
| 3 | Thursday, March 19 | Modules 1-3 (Propositional Logic, Informed Search, Advanced Search/Optimization) | ✅ Complete | Module 3 implementation: `Module 3/monte_carlo_simulator.py`, `Module 3/bet_sizing_optimizer.py`, `Module 3/strategy_evaluator.py`; Unit tests: `unit_tests/Module 3/test_module3_monte_carlo.py`; Demo: `Module 3/demo_module3.py`; Review: `docs/checkpoint_3_code_review.md` |
| 4 | Thursday, April 2 | Modules 1-4 (All except Reinforcement Learning) | [Status to be updated] | [Evidence to be added] |
| 5 | Thursday, April 16 | Modules 1-5 (Complete system) | [Status to be updated] | [Evidence to be added] |

## Required Workflow (Agent-Guided)

Before each module:

1. Write a short module spec in this README (inputs, outputs, dependencies, tests).
2. Ask the agent to propose a plan in "Plan" mode.
3. Review and edit the plan. You must understand and approve the approach.
4. Implement the module in the appropriate module directory (e.g., `Module 1/`).
5. Unit test the module, placing tests in `unit_tests/` (parallel structure to module directories).
6. Run a rubric review using the code-review skill at `.claude/skills/code-review/SKILL.md`.

Keep `AGENTS.md` updated with your module plan, constraints, and links to APIs/data sources.

## References

**Project Documentation:**
- Project Instructions: https://csc-343.path.app/projects/project-2-ai-system/ai-system.project.md
- Code elegance rubric: https://csc-343.path.app/rubrics/code-elegance.rubric.md
- Course schedule: https://csc-343.path.app/resources/course.schedule.md
- Rubric: https://csc-343.path.app/projects/project-2-ai-system/ai-system.rubric.md

**Libraries and APIs:**
- [To be added as modules are implemented]

**Datasets:**
- [To be added if external datasets are used]

**Poker Strategy References:**
- [Known heads-up pre-flop Nash equilibrium solutions to be referenced]
- [Hand equity/ranking tables to be referenced]
