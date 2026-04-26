## Project Context

- System title: # Heads-Up Pre-Flop Poker: Comparative Analysis of AI Agent Strategies
- Theme: Poker
- Project Plan:


**Module plan:**

## System Overview

This system provides a comprehensive platform for playing heads-up (two-player) Texas Hold'em pre-flop poker against AI agents, each implementing different AI techniques. The system integrates multiple AI paradigms to create four distinct agents: a rule-based agent using propositional logic and A* search; a Monte Carlo simulation agent; an LLM-based strategy agent; and an adaptive learning agent using reinforcement learning. Users can compete against any agent, and the system enables agent-versus-agent competitions to quantitatively compare the effectiveness of different AI approaches.

Poker is an ideal domain for exploring AI concepts because it combines incomplete information, strategic decision-making, and optimization challenges. The pre-flop phase provides a manageable scope while still requiring sophisticated analysis. By implementing each AI technique as a playable agent and enabling direct comparison, this system demonstrates how different AI paradigms perform in practice, revealing trade-offs between speed and accuracy, exploitation and unexploitability, and rule-based versus learning-based approaches. This comparative analysis makes the system both educationally valuable and practically useful for understanding AI strategy optimization.

### Agents

- **Agent 1 – Rule-Based + Search**: Uses Module 1 (Propositional Logic) to determine playability and Module 2 (A* Search) to find optimal bet sizes.
- **Agent 2 – Monte Carlo**: Uses Module 3 to compute optimal opening actions via Monte Carlo simulation (no heuristics or closed-form EV).
- **Agent 3 – LLM Strategy Agent**: Uses Module 4 to make context-aware poker decisions with structured prompts and reasoning output.
- **Agent 4 – Adaptive Learning**: Uses Module 5 (Reinforcement Learning) to learn and exploit opponent tendencies over time.

## Modules

### Module 1: Rule-Based Decision Framework

**Topics:** Propositional Logic (Knowledge Bases, Inference Methods, Chaining, CNF)

**Input:** Starting hand (e.g., "Ace-King suited"), position (Button or Big Blind), stack size in big blinds (integer), opponent tendency category (dropdown: "Tight", "Loose", "Aggressive", "Passive", "Unknown")

**Output:** Knowledge base of propositional logic rules encoded in CNF format. Rules specify conditions for playing hands, such as: IF (position = Button) AND (hand_strength >= top_30_percent) AND (stack_size > 20) THEN (playable = true). Output includes rule set as a structured knowledge base that can be queried for decision support.

**Integration:** This module establishes the foundational rule framework that subsequent modules reference. The knowledge base provides logical constraints that inform search algorithms (e.g., "only consider hands that satisfy these rules") and serves as a baseline for game theory and reinforcement learning modules to build upon or adapt.

**Prerequisites:** Course content on Propositional Logic, Knowledge Bases, CNF conversion, and inference methods.

---

### Module 2: Optimal Bet Sizing Search

**Topics:** Informed Search (A*), Optimization

**Input:** Starting hand (string), position (Button/Big Blind), stack sizes (tuple: (your_stack, opponent_stack) in big blinds), opponent tendency category (string), knowledge base from Module 1 (CNF rules). The module also uses an expected value evaluation function that computes EV for any given bet size; to keep this simple, EV is computed using fixed fold/call/raise probabilities per opponent tendency category plus pre-existing hand equity/ranking tables.

**Output:** Optimal bet size as a multiple of the big blind (float, e.g., 3.0 for "3x big blind"). Output includes the specific action recommendation (fold, call, or raise to X big blinds) and the expected value of that action. If the hand is not playable according to Module 1 rules, output is "fold".

**Integration:** This module uses the rule-based constraints from Module 1 to filter search space (only searches bet sizes for hands that satisfy the rules). The optimal bet sizing output informs Module 3's strategy construction and can optionally be provided as context to Module 4 (LLM agent).

**Prerequisites:** Course content on Informed Search algorithms (A*), heuristic functions, and optimization. Module 1 (Rule-Based Decision Framework) for constraint filtering.

---

### Module 3: Monte Carlo Optimal Opening Actions

**Topics:** Monte Carlo Methods, Optimization

**Input:** Position (Button/Big Blind), stack sizes (tuple), opponent tendency category (string). This module does not depend on Module 1 or Module 2; optimal opening actions are derived purely from Monte Carlo simulation (no Module 2 heuristics or closed-form EV formulas), so it can serve as a standalone agent competing against the Module 1–2 agent.

**Output:** Optimal opening action strategy (e.g., fold or open to X BB per hand or range), computed by simulation rather than heuristics or closed-form EV. Output includes expected value of the strategy and confidence intervals from simulation. May include a list of hands and their recommended opening actions (fold or bet size).

**Integration:** This module uses Monte Carlo simulation to compute optimal opening actions directly: it simulates many outcomes (e.g., opponent responses, hand runouts) and chooses actions that maximize simulated value. It does not use Module 2's heuristics or EV formulas. The resulting strategy provides an alternative approach to bet sizing that complements the search-based method.

**Prerequisites:** Course content on Monte Carlo methods and optimization.

---

### Module 4: LLM-Based Poker Strategy Agent

**Topics:** Large Language Models, Prompt Engineering, Tool-Augmented Decision Making

**Input:** Current game state (hand, position, stack sizes, pot, prior actions), optional outputs from Modules 1-3 (rule constraints, search recommendations, Monte Carlo confidence intervals), and structured prompt templates.

**Output:** Action recommendation (fold/call/raise with size), natural-language reasoning trace, and confidence score. Output format: dictionary with selected action, bet size, explanation, and optional references to supporting module signals.

**Integration:** This module transforms structured game context into an LLM prompt and returns a playable decision. It can optionally incorporate Module 1 constraints and Module 2/3 recommendations as context, while remaining a distinct LLM-driven agent.

**Prerequisites:** Course content on language models, prompt design, and model evaluation. Modules 1-3 (optional) for structured context features.

---

### Module 5: Adaptive Opponent Exploitation

**Topics:** Reinforcement Learning (MDP, Policy, Value Functions, Q-Learning)

**Input:** Historical game data (list of tuples: (hand, position, action_taken, opponent_action, outcome, reward)), opponent tendency category (string), and optional baseline signals from Modules 1-4.

**Output:** Learned policy (dictionary mapping (hand, position, opponent_tendency) to optimal action with Q-values), exploitation strategy recommendations, and updated action-value estimates (Q-table or function approximation).

**Integration:** This module trains an RL policy that adapts decisions from interaction outcomes and opponent behavior over time. It can be initialized from other module recommendations but ultimately learns from experience.

**Prerequisites:** Course content on Reinforcement Learning, MDPs, Q-Learning, and policy learning. Modules 1-4 (optional) for initialization and comparison baselines.


## Feasibility Study

_A timeline showing that each module's prerequisites align with the course schedule. Verify that you are not planning to implement content before it is taught._

| Module | Required Topic(s) | Topic Covered By | Checkpoint Due |
| ------ | ----------------- | ---------------- | -------------- |
| 1      | Propositional Logic | Week 2 | Wednesday, Feb 11  |
| 2      | Informed Search (A*) | Week 3 | Thursday, Feb 26 |
| 3      | Advanced Search/Optimization | Week 5.5 | Thursday, March 19 |
| 4      | LLM Agent Design & Prompt Engineering | Week 7 | Thursday, April 2 |
| 5      | Reinforcement Learning | Week 10 | Thursday, April 16 |

## Coverage Rationale

This topic selection fits poker strategy analysis naturally. **Propositional Logic** encodes fundamental decision rules (position-based constraints, hand strength relationships) that establish the knowledge foundation. **Search algorithms** (A*) are essential for finding optimal bet sizes by exploring action spaces efficiently. **Monte Carlo Methods** provide a simulation-based approach to optimization, computing optimal opening actions through sampling rather than heuristics or closed-form EV formulas. **LLM-based reasoning** provides flexible context-aware strategy decisions with explainable outputs. **Reinforcement Learning** enables adaptive learning from opponent behavior, a critical capability for exploitation over time.

The progression from rules → search → simulation → LLM reasoning → learning demonstrates how different AI paradigms complement each other. Each topic addresses a distinct aspect: logic provides structure, search finds solutions, simulation estimates values, LLMs provide contextual reasoning, and RL enables adaptation.

Trade-offs considered: Supervised Learning could predict opponent actions but was omitted to focus on strategic optimization. First-Order Logic could encode more complex relationships but Propositional Logic suffices for pre-flop rules. For LLM-based decisions, output quality depends on prompt design and guardrails; this is mitigated with structured prompts and action validation. The focus on pre-flop (rather than full game trees) makes the system feasible while still demonstrating all required concepts effectively. Organizing modules as agents and comparing them adds minimal complexity while providing significant educational and research value.

## Constraints

- 5-6 modules total, each tied to course topics.
- Each module must have clear inputs/outputs and tests.
- Align module timing with the course schedule.

## How the Agent Should Help

- Draft plans for each module before coding.
- Suggest clean architecture and module boundaries.
- Identify missing tests and edge cases.
- Review work against the rubric using the code-review skill.

## Agent Workflow

1. Ask for the current module spec from `README.md`.
2. Produce a plan (use "Plan" mode if available).
3. Wait for approval before writing or editing code.
4. After implementation, run the code-review skill and list gaps.

## Key References

- Project Instructions: https://csc-343.path.app/projects/project-2-ai-system/ai-system.project.md
- Code elegance rubric: https://csc-343.path.app/rubrics/code-elegance.rubric.md
- Course schedule: https://csc-343.path.app/resources/course.schedule.md
- Rubric: https://csc-343.path.app/projects/project-2-ai-system/ai-system.rubric.md
