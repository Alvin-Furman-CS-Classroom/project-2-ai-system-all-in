# Heads-Up Pre-Flop Poker Strategy Analyzer

## System Overview

This system provides strategic analysis for heads-up (two-player) Texas Hold'em play, helping players make optimal decisions based on starting hands, position, stack sizes, and opponent tendencies. The system integrates multiple AI techniques to deliver actionable insights: propositional logic encodes fundamental poker rules and constraints; optimization and A* search optimize bet sizing for specific hands; Monte Carlo simulation computes optimal opening actions directly (without heuristics or EV formulas); game theory provides Nash equilibrium baseline strategies; a full-hand strategy module expands pre-flop strategies to play an entire hand; and reinforcement learning adapts to exploit specific opponent types.

Poker is an ideal domain for exploring AI concepts because it combines incomplete information, strategic decision-making, and optimization challenges. Each module builds upon previous work: rules establish the foundation, search and optimization find optimal actions, Monte Carlo computes opening strategies via simulation, game theory provides theoretical baselines, full-hand play extends strategies beyond pre-flop, and reinforcement learning enables adaptive exploitation. This progression demonstrates how different AI paradigms complement each other in a unified system, making it both educationally valuable and practically useful for poker players seeking to improve their strategic understanding.

## Modules

### Module 1: Rule-Based Decision Framework

**Topics:** Propositional Logic (Knowledge Bases, Inference Methods, Chaining, CNF)

**Input:** Starting hand (e.g., "Ace-King suited"), position (Button or Big Blind), stack size in big blinds (integer), opponent tendency category (dropdown: "Tight", "Loose", "Aggressive", "Passive", "Unknown")

**Output:** Knowledge base of propositional logic rules encoded in CNF format. Rules specify conditions for playing hands, such as: IF (position = Button) AND (hand_strength >= top_30_percent) AND (stack_size > 20) THEN (playable = true). Output includes rule set as a structured knowledge base that can be queried for decision support.

**Integration:** This module establishes the foundational rule framework that subsequent modules reference. The knowledge base provides logical constraints that inform search algorithms (e.g., "only consider hands that satisfy these rules") and serves as a baseline for game theory and reinforcement learning modules to build upon or adapt.

**Prerequisites:** Course content on Propositional Logic, Knowledge Bases, CNF conversion, and inference methods.

---

### Module 2: Optimal Bet Sizing Search

**Topics:** Optimization, Informed Search (A*)

**Input:** Starting hand (string), position (Button/Big Blind), stack sizes (tuple: (your_stack, opponent_stack) in big blinds), opponent tendency category (string), knowledge base from Module 1 (CNF rules). The module also uses an expected value evaluation function that computes EV for any given bet size; to keep this simple, EV is computed using fixed fold/call/raise probabilities per opponent tendency category plus pre-existing hand equity/ranking tables.

**Output:** Optimal bet size as a multiple of the big blind (float, e.g., 3.0 for "3x big blind"). Output includes the specific action recommendation (fold, call, or raise to X big blinds) and the expected value of that action. If the hand is not playable according to Module 1 rules, output is "fold".

**Integration:** This module uses the rule-based constraints from Module 1 to filter search space (only searches bet sizes for hands that satisfy the rules). The optimal bet sizing output provides action-level recommendations for use elsewhere; Module 3 independently uses Monte Carlo to compute optimal opening actions.

**Prerequisites:** Course content on Informed Search (A*), heuristic functions, and optimization. Module 1 (Rule-Based Decision Framework) for constraint filtering.

---

### Module 3: Monte Carlo Optimal Opening Actions

**Topics:** Monte Carlo Methods, Optimization

**Input:** Position (Button/Big Blind), stack sizes (tuple), opponent tendency category (string), optional knowledge base from Module 1 (for playability filtering). No dependency on Module 2; optimal opening actions are derived purely from Monte Carlo simulation.

**Output:** Optimal opening action strategy (e.g., fold or open to X BB per hand or range), computed by simulation rather than heuristics or closed-form EV. Output includes expected value of the strategy and confidence intervals from simulation. May include a list of hands and their recommended opening actions (fold or bet size).

**Integration:** This module uses Monte Carlo simulation to compute optimal opening actions directly: it simulates many outcomes (e.g., opponent responses, runouts) and chooses actions that maximize simulated value. It does not use Module 2's heuristics or EV formulas. The resulting strategy informs Module 5's full-hand strategy and Module 6's reinforcement learning. Module 4 does not depend on Module 3.

**Prerequisites:** Course content on Monte Carlo methods and optimization. Module 1 (optional) for rule constraints or playability filtering.

---

### Module 4: Nash Equilibrium Strategy Analysis

**Topics:** Games and Game Theory (Nash Equilibrium)

**Input:** Position (Button/Big Blind), stack sizes (tuple), optional knowledge base from Module 1. The module does not depend on Module 2 or Module 3. It references known heads-up pre-flop Nash equilibrium solutions (from established poker solvers or published research) as baseline strategies.

**Output:** Nash equilibrium reference data: equilibrium frequencies and mixed strategies for key pre-flop decision points. Output format: dictionary with equilibrium strategies, comparison metrics (how a given strategy deviates from equilibrium, if one is provided), and exploitability analysis where applicable.

**Integration:** This module provides the Nash equilibrium baseline for pre-flop play independently of Modules 2 and 3. The equilibrium reference establishes a theoretical baseline for Module 5 (full-hand strategy) and Module 6 (reinforcement learning); other modules may optionally compare their strategies against it.

**Prerequisites:** Course content on Game Theory and Nash Equilibrium. Module 1 (optional) for rule constraints.

---

### Module 5: Full-Hand Strategy (Beyond Pre-Flop)

**Topics:** Strategy Extension, Decision Trees / State-Space Search (as applicable)

**Input:** Pre-flop strategies from Modules 1–4 (playable hands, bet sizes, Nash reference), position, stack sizes, opponent tendency. For post-flop: community cards, pot size, and current street (flop, turn, river).

**Output:** Strategy recommendations for playing an entire hand: pre-flop action (from prior modules) plus post-flop action recommendations (e.g., bet/check/fold/call on flop, turn, river). Output may include simplified decision rules or lookup tables for key situations.

**Integration:** This module expands the system from pre-flop-only to full-hand play. It builds on Modules 1–4 by extending their outputs to later streets, providing a bridge from pre-flop analysis to complete hand strategy. Module 6 (Reinforcement Learning) can then adapt these full-hand strategies based on opponent behavior.

**Prerequisites:** Modules 1, 2, 3, and 4. Course content on decision-making under uncertainty and (optionally) search or decision trees as needed for post-flop abstraction.

---

### Module 6: Adaptive Opponent Exploitation

**Topics:** Reinforcement Learning (MDP, Policy, Value Functions, Q-Learning)

**Input:** Historical game data (list of tuples: (hand, position, action_taken, opponent_action, outcome, reward)), opponent tendency category (string), equilibrium reference data from Module 4 (baseline policy for comparison), strategies from Module 3 and Module 5 (bet sizing and full-hand play).

**Output:** Learned policy (dictionary mapping (hand, position, opponent_tendency) to optimal action with Q-values), exploitation strategy recommendations (how to deviate from Nash equilibrium to exploit opponent weaknesses). Output includes action-value function (Q-table or function approximation) and updated strategy recommendations.

**Integration:** This module learns to adapt strategies based on opponent behavior, using Module 4's equilibrium reference data as a baseline and Module 3's bet sizing and Module 5's full-hand strategies as starting points. The final system output combines all modules to provide opponent-specific optimal strategies.

**Prerequisites:** Course content on Reinforcement Learning, MDPs, Q-Learning, and policy learning. Modules 1, 3, 4, and 5 for foundational knowledge, bet sizing, equilibrium baselines, and full-hand strategies.


## Feasibility Study

_A timeline showing that each module's prerequisites align with the course schedule. Verify that you are not planning to implement content before it is taught._

| Module | Required Topic(s) | Topic Covered By | Checkpoint Due |
| ------ | ----------------- | ---------------- | -------------- |
| 1      | Propositional Logic | Week 2 | Wednesday, Feb 11  |
| 2      | Informed Search (A*), Optimization | Week 3 | Thursday, Feb 26 |
| 3      | Monte Carlo, Optimization | Week 5.5 | Thursday, March 19 |
| 4      | Game Theory (Nash Equilibrium) | Week 7 | Thursday, April 2 |
| 5      | Strategy Extension / Full-Hand Play | TBD | TBD |
| 6      | Reinforcement Learning | Week 10 | Thursday, April 16 |

## Coverage Rationale

This topic selection fits poker strategy analysis naturally. **Propositional Logic** encodes fundamental decision rules that establish the knowledge foundation. **Optimization and A*** find optimal bet sizes by exploring the action space efficiently. **Monte Carlo** computes optimal opening actions through simulation (no heuristics or EV formulas). **Nash Equilibrium** provides theoretical baselines for pre-flop play. **Full-hand strategy** extends the system beyond pre-flop to play an entire hand. **Reinforcement Learning** enables adaptive exploitation of opponent weaknesses.

The progression from rules → search/optimization → Monte Carlo → game theory → full-hand play → learning demonstrates how different AI paradigms complement each other. Each topic addresses a distinct aspect: logic provides structure, A* and optimization find solutions, Monte Carlo computes opening actions via simulation, Nash equilibrium establishes baselines, full-hand play extends scope, and RL enables adaptation.

Trade-offs considered: Supervised Learning could predict opponent actions but was omitted to focus on strategic optimization. First-Order Logic could encode more complex relationships but Propositional Logic suffices for pre-flop rules. For Game Theory, computing Nash equilibrium from scratch would be computationally intensive; instead, the system references known equilibrium solutions. Module 5 (full-hand) keeps post-flop abstraction manageable while extending the system beyond pre-flop.
