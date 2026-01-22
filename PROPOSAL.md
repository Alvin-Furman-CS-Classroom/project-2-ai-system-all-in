# Heads-Up Pre-Flop Poker Strategy Analyzer

## System Overview

This system provides strategic analysis for heads-up (two-player) Texas Hold'em pre-flop play, helping players make optimal decisions based on starting hands, position, stack sizes, and opponent tendencies. The system integrates multiple AI techniques to deliver actionable insights: propositional logic encodes fundamental poker rules and constraints; search algorithms optimize bet sizing for specific hands; advanced optimization determines optimal opening ranges; game theory computes Nash equilibrium baseline strategies; and reinforcement learning adapts to exploit specific opponent types.

Poker is an ideal domain for exploring AI concepts because it combines incomplete information, strategic decision-making, and optimization challenges. The pre-flop phase provides a manageable scope while still requiring sophisticated analysis. Each module builds upon previous work: rules establish the foundation, search finds optimal actions, game theory provides theoretical baselines, and reinforcement learning enables adaptive exploitation. This progression demonstrates how different AI paradigms complement each other in a unified system, making it both educationally valuable and practically useful for poker players seeking to improve their strategic understanding.

## Modules

### Module 1: Rule-Based Decision Framework

**Topics:** Propositional Logic (Knowledge Bases, Inference Methods, Chaining, CNF)

**Input:** Starting hand (e.g., "Ace-King suited"), position (Button or Big Blind), stack size in big blinds (integer), opponent tendency category (dropdown: "Tight", "Loose", "Aggressive", "Passive", "Unknown")

**Output:** Knowledge base of propositional logic rules encoded in CNF format. Rules specify conditions for playing hands, such as: IF (position = Button) AND (hand_strength >= top_30_percent) AND (stack_size > 20) THEN (playable = true). Output includes rule set as a structured knowledge base that can be queried for decision support.

**Integration:** This module establishes the foundational rule framework that subsequent modules reference. The knowledge base provides logical constraints that inform search algorithms (e.g., "only consider hands that satisfy these rules") and serves as a baseline for game theory and reinforcement learning modules to build upon or adapt.

**Prerequisites:** Course content on Propositional Logic, Knowledge Bases, CNF conversion, and inference methods.

---

### Module 2: Optimal Bet Sizing Search

**Topics:** Informed Search (A*, IDA*, Beam Search), Optimization

**Input:** Starting hand (string), position (Button/Big Blind), stack sizes (tuple: (your_stack, opponent_stack) in big blinds), opponent tendency category (string), knowledge base from Module 1 (CNF rules). The module also uses an expected value evaluation function that computes EV for any given bet size; to keep this simple, EV is computed using fixed fold/call/raise probabilities per opponent tendency category plus pre-existing hand equity/ranking tables.

**Output:** Optimal bet size as a multiple of the big blind (float, e.g., 3.0 for "3x big blind"). Output includes the specific action recommendation (fold, call, or raise to X big blinds) and the expected value of that action. If the hand is not playable according to Module 1 rules, output is "fold".

**Integration:** This module uses the rule-based constraints from Module 1 to filter search space (only searches bet sizes for hands that satisfy the rules). The optimal bet sizing output informs Module 3's range construction (which hands to play at which bet sizes) and provides action-level recommendations that Module 4 (Game Theory) can compare against Nash equilibrium strategies.

**Prerequisites:** Course content on Informed Search algorithms (A*, IDA*, Beam Search), heuristic functions, and optimization. Module 1 (Rule-Based Decision Framework) for constraint filtering.

---

### Module 3: Opening Range Optimization

**Topics:** Advanced Search (Hill Climbing, Simulated Annealing, Genetic Algorithms), Optimization

**Input:** Position (Button/Big Blind), stack sizes (tuple), opponent tendency category (string), knowledge base from Module 1, bet sizing recommendations from Module 2 (dictionary mapping hands to optimal bet sizes).

**Output:** Optimal opening range as a percentage of starting hands (float, e.g., 0.40 for "top 40% of hands") and a list of specific hands to play from that position (list of hand strings, e.g., ["AA", "AKs", "AKo", "AQs", ...]). Output includes expected value of the overall range strategy.

**Integration:** This module optimizes which hands to include in an opening range, using Module 2's bet sizing recommendations to evaluate range profitability. The optimized ranges provide strategic context for Module 4's game theory analysis (comparing constructed ranges to Nash equilibrium) and inform Module 5's reinforcement learning (establishing baseline ranges to adapt from).

**Prerequisites:** Course content on Advanced Search algorithms (Hill Climbing, Simulated Annealing, Genetic Algorithms) and optimization techniques. Modules 1 and 2 for rule constraints and bet sizing data.

---

### Module 4: Nash Equilibrium Strategy Analysis

**Topics:** Games and Game Theory (Minimax, Nash Equilibrium, Mixed Strategies)

**Input:** Position (Button/Big Blind), stack sizes (tuple), optimized strategies from Modules 2 and 3 (bet sizing recommendations and opening ranges), knowledge base from Module 1. The module references known heads-up pre-flop Nash equilibrium solutions (from established poker solvers or published research) as baseline strategies.

**Output:** Comparative analysis including: (1) deviation metrics comparing optimized strategies to Nash equilibrium (how different are bet sizes/ranges from equilibrium?), (2) exploitability analysis (how exploitable are the optimized strategies?), (3) equilibrium reference data (equilibrium frequencies and mixed strategies for key decision points). Output format: dictionary with comparison metrics, exploitability scores, and equilibrium reference strategies.

**Integration:** This module analyzes how the optimized strategies from Modules 2 and 3 compare to theoretical optimal play (Nash equilibrium). The equilibrium reference provides a baseline for Module 2's search results (evaluating how close optimized bet sizes are to equilibrium) and establishes a starting point for Module 5's reinforcement learning (identifying profitable deviations from equilibrium to exploit opponents).

**Prerequisites:** Course content on Game Theory, Nash Equilibrium, Minimax, and mixed strategies. Modules 1, 2, and 3 for rule constraints, bet sizing, and range data to compare against equilibrium.

---

### Module 5: Adaptive Opponent Exploitation

**Topics:** Reinforcement Learning (MDP, Policy, Value Functions, Q-Learning)

**Input:** Historical game data (list of tuples: (hand, position, action_taken, opponent_action, outcome, reward)), opponent tendency category (string), equilibrium reference data from Module 4 (baseline policy for comparison), opening ranges from Module 3.

**Output:** Learned policy (dictionary mapping (hand, position, opponent_tendency) to optimal action with Q-values), exploitation strategy recommendations (how to deviate from Nash equilibrium to exploit opponent weaknesses). Output includes action-value function (Q-table or function approximation) and updated strategy recommendations.

**Integration:** This module learns to adapt strategies based on opponent behavior, using Module 4's equilibrium reference data as a baseline and Module 3's ranges as starting points. The learned exploitation strategies complement Module 2's search-based optimization (providing adaptive bet sizing) and Module 3's range optimization (suggesting range adjustments against specific opponents). The final system output combines all modules to provide opponent-specific optimal strategies.

**Prerequisites:** Course content on Reinforcement Learning, MDPs, Q-Learning, and policy learning. Modules 1, 3, and 4 for foundational knowledge, ranges, and equilibrium baselines.


## Feasibility Study

_A timeline showing that each module's prerequisites align with the course schedule. Verify that you are not planning to implement content before it is taught._

| Module | Required Topic(s) | Topic Covered By | Checkpoint Due |
| ------ | ----------------- | ---------------- | -------------- |
| 1      | Propositional Logic | Week 2 | Wednesday, Feb 11  |
| 2      | Informed Search (A*, IDA*, Beam Search) | Week 3 | Thursday, Feb 26 |
| 3      | Advanced Search/Optimization | Week 5.5 | Thursday, March 19 |
| 4      | Game Theory (Nash Equilibrium) | Week 7 | Thursday, April 2 |
| 5      | Reinforcement Learning | Week 10 | Thursday, April 16 |

## Coverage Rationale

This topic selection fits poker strategy analysis naturally. **Propositional Logic** encodes fundamental decision rules (position-based constraints, hand strength relationships) that establish the knowledge foundation. **Search algorithms** (A*, IDA*, Beam Search) are essential for finding optimal bet sizes by exploring action spaces efficiently, while **Advanced Search/Optimization** (Hill Climbing, Simulated Annealing, Genetic Algorithms) optimizes complex strategy spaces (opening ranges) where exhaustive search is infeasible. **Game Theory** provides theoretical baselines through Nash equilibrium analysis and comparison, which is central to evaluating optimal poker strategy. **Reinforcement Learning** enables adaptive learning from opponent behavior, a critical capability for exploiting weaknesses.

The progression from rules → search → optimization → game theory → learning demonstrates how different AI paradigms complement each other. Each topic addresses a distinct aspect: logic provides structure, search finds solutions, optimization refines strategies, game theory establishes baselines, and RL enables adaptation.

Trade-offs considered: Supervised Learning could predict opponent actions but was omitted to focus on strategic optimization. First-Order Logic could encode more complex relationships but Propositional Logic suffices for pre-flop rules. For Game Theory, computing Nash equilibrium from scratch would be computationally intensive; instead, the system references known equilibrium solutions and focuses on comparative analysis, which demonstrates game theory concepts while remaining feasible. The focus on pre-flop (rather than full game trees) makes the system feasible while still demonstrating all required concepts effectively.