# Heads-Up Pre-Flop Poker Strategy Analyzer

## Overview

This system provides strategic analysis for heads-up (two-player) Texas Hold'em pre-flop play, helping players make optimal decisions based on starting hands, position, stack sizes, and opponent tendencies. The system integrates multiple AI techniques to deliver actionable insights: propositional logic encodes fundamental poker rules and constraints; search algorithms optimize bet sizing for specific hands; advanced optimization determines optimal opening ranges; game theory computes Nash equilibrium baseline strategies; and reinforcement learning adapts to exploit specific opponent types.

Poker is an ideal domain for exploring AI concepts because it combines incomplete information, strategic decision-making, and optimization challenges. The pre-flop phase provides a manageable scope while still requiring sophisticated analysis. Each module builds upon previous work: rules establish the foundation, search finds optimal actions, game theory provides theoretical baselines, and reinforcement learning enables adaptive exploitation. This progression demonstrates how different AI paradigms complement each other in a unified system, making it both educationally valuable and practically useful for poker players seeking to improve their strategic understanding.

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
| 3 | Advanced Search/Optimization (Hill Climbing, Simulated Annealing, Genetic Algorithms) | Position, stack sizes, opponent tendency, Module 1 knowledge base, Module 2 bet sizing recommendations | Optimal opening range (percentage and list of hands), expected value of range strategy | Modules 1, 2 | Thursday, March 19 |
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

Module 1 is implemented and ready to use.

Dependencies:
- Python 3.7+ (for dataclasses support)
- Standard library only (typing, dataclasses)

Setup steps:
1. Clone the repository
2. Ensure Python 3.7+ is installed
3. No additional package installation required (uses only standard library)

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
- Module 2: `[command to be added]`
- Module 3: `[command to be added]`
- Module 4: `[command to be added]`
- Module 5: `[command to be added]`

## Testing

**Unit Tests** (`unit_tests/`): Mirror the structure of module directories. Each module has corresponding unit tests.

**Integration Tests** (`integration_tests/`): Create a new subfolder for each module beyond the first, demonstrating how modules work together.

Test commands:
- Run Module 1 unit tests: `python3 -m unittest "unit_tests/Module 1/test_propositional_logic.py" -v`
- Run all unit tests: `python3 -m unittest discover unit_tests -v`
- Run integration tests: `[command to be added]` (for future modules)

Test data:
- Module 1 tests cover: all hand types, positions, opponent types, stack sizes, edge cases, and backward chaining scenarios
- 49 unit tests covering all functionality

## Checkpoint Log

| Checkpoint | Date | Modules Included | Status | Evidence |
| ---------- | ---- | ---------------- | ------ | -------- |
| 1 | Wednesday, Feb 11 | Module 1 (Propositional Logic) | ✅ Complete | Implementation: `Module 1/propositional_logic.py`, Tests: `unit_tests/Module 1/test_propositional_logic.py` (49 tests), Reports: `checkpoint_1_elegance_report.md`, `checkpoint_1_module_report.md` |
| 2 | Thursday, Feb 26 | Modules 1-2 (Propositional Logic, Informed Search) | [Status to be updated] | [Evidence to be added] |
| 3 | Thursday, March 19 | Modules 1-3 (Propositional Logic, Informed Search, Advanced Search/Optimization) | [Status to be updated] | [Evidence to be added] |
| 4 | Thursday, April 2 | Modules 1-4 (All except Reinforcement Learning) | [Status to be updated] | [Evidence to be added] |
| 5 | Thursday, April 16 | Modules 1-5 (Complete system) | [Status to be updated] | [Evidence to be added] |

## Required Workflow (Agent-Guided)

Before each module:

1. Write a short module spec in this README (inputs, outputs, dependencies, tests).
2. Ask the agent to propose a plan in "Plan" mode.
3. Review and edit the plan. You must understand and approve the approach.
4. Implement the module in the appropriate module directory (e.g., `Module 1/`).
5. Unit test the module, placing tests in `unit_tests/` (parallel structure to module directories).
6. For modules beyond the first, add integration tests in `integration_tests/` (new subfolder per module).
7. Run a rubric review using the code-review skill at `.claude/skills/code-review/SKILL.md`.

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
