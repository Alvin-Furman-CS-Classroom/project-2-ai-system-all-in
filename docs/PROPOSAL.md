# Heads-Up Pre-Flop Poker: Comparative Analysis of AI Agent Strategies

## System Overview

This system provides a comprehensive platform for playing heads-up (two-player) Texas Hold'em pre-flop poker against AI agents, each implementing different AI techniques. The system integrates multiple AI paradigms to create four distinct agents: a rule-based agent using propositional logic and A* search; a Monte Carlo simulation agent; an LLM-based strategy agent; and an adaptive learning agent using reinforcement learning. Users can compete against any agent, and the system enables agent-versus-agent competitions to quantitatively compare the effectiveness of different AI approaches.

Poker is an ideal domain for exploring AI concepts because it combines incomplete information, strategic decision-making, and optimization challenges. The pre-flop phase provides a manageable scope while still requiring sophisticated analysis. By implementing each AI technique as a playable agent and enabling direct comparison, this system demonstrates how different AI paradigms perform in practice, revealing trade-offs between speed and accuracy, exploitation and unexploitability, and rule-based versus learning-based approaches. This comparative analysis makes the system both educationally valuable and practically useful for understanding AI strategy optimization.

## Core Innovation: Agent Comparison System

Unlike traditional systems that implement modules in isolation, this project organizes AI modules as **playable agents** and enables **direct comparison** through:
1. **User vs. Agent Competition**: Users can play against any of the four agents
2. **Agent vs. Agent Competition**: Automated tournaments to determine which approach is most effective
3. **Quantitative Analysis**: Win rates, expected value, and performance metrics for each agent
4. **Educational Insights**: Demonstrates strengths and weaknesses of each AI technique

## Modules

### Module 1: Rule-Based Decision Framework

**Topics:** Propositional Logic (Knowledge Bases, Inference Methods, Chaining, CNF)

**Input:** Starting hand (e.g., "Ace-King suited", "AA", "AKs"), position (Button or Big Blind), stack size in big blinds (integer), opponent tendency category ("Tight", "Loose", "Aggressive", "Passive", "Unknown")

**Output:** Knowledge base of propositional logic rules encoded in CNF format. Rules specify conditions for playing hands, such as: IF (position = Button) AND (hand_strength >= top_30_percent) AND (stack_size > 20) THEN (playable = true). Output includes rule set as a structured knowledge base that can be queried for decision support, along with an inference chain showing how the decision was derived.

**Integration:** This module establishes the foundational rule framework. The knowledge base provides logical constraints that inform search algorithms (e.g., "only consider hands that satisfy these rules") and serves as a baseline for game theory and reinforcement learning modules to build upon or adapt.

**Agent Usage:** Used by **Agent 1 (Rule-Based + Search Agent)** to determine hand playability before bet sizing optimization.

**Prerequisites:** Course content on Propositional Logic, Knowledge Bases, CNF conversion, and inference methods.

---

### Module 2: Optimal Bet Sizing Search

**Topics:** Informed Search (A*, IDA*, Beam Search), Optimization

**Input:** Starting hand (string), position (Button/Big Blind), stack sizes (tuple: (your_stack, opponent_stack) in big blinds), opponent tendency category (string), knowledge base from Module 1 (CNF rules). The module uses an expected value evaluation function that computes EV for any given bet size using fixed fold/call/raise probabilities per opponent tendency category plus pre-existing hand equity/ranking tables.

**Output:** Optimal bet size as a multiple of the big blind (float, e.g., 3.0 for "3x big blind"). Output includes the specific action recommendation (fold, call, or raise to X big blinds) and the expected value of that action. If the hand is not playable according to Module 1 rules, output is "fold".

**Integration:** This module uses the rule-based constraints from Module 1 to filter search space (only searches bet sizes for hands that satisfy the rules). The optimal bet sizing output provides action-level recommendations. The A* search algorithm explores the bet size space efficiently using heuristics to estimate maximum achievable EV.

**Agent Usage:** Used by **Agent 1 (Rule-Based + Search Agent)** to find optimal bet sizes after Module 1 determines playability.

**Prerequisites:** Course content on Informed Search algorithms (A*, IDA*, Beam Search), heuristic functions, and optimization. Module 1 (Rule-Based Decision Framework) for constraint filtering.

---

### Module 3: Monte Carlo Optimal Opening Actions

**Topics:** Monte Carlo Methods, Optimization

**Input:** Position (Button/Big Blind), stack sizes (tuple), opponent tendency category (string), optional knowledge base from Module 1 (for playability filtering). This module operates independently of Module 2; optimal opening actions are derived purely from Monte Carlo simulation without using heuristics or closed-form EV formulas.

**Output:** Optimal opening action strategy (e.g., fold or open to X BB per hand or range), computed by simulation rather than heuristics or closed-form EV. Output includes expected value of the strategy and confidence intervals from simulation. May include a list of hands and their recommended opening actions (fold or bet size).

**Integration:** This module uses Monte Carlo simulation to compute optimal opening actions directly: it simulates many outcomes (e.g., opponent responses, hand runouts) and chooses actions that maximize simulated value. It does not use Module 2's heuristics or EV formulas. The resulting strategy provides an alternative approach to bet sizing that complements the search-based method.

**Agent Usage:** Used by **Agent 2 (Monte Carlo Agent)** as its primary decision-making mechanism.

**Prerequisites:** Course content on Monte Carlo methods and optimization. Module 1 (optional) for rule constraints or playability filtering.

---

### Module 4: LLM-Based Poker Strategy Agent

**Topics:** Large Language Models, Prompt Engineering, Tool-Augmented Decision Making

**Input:** Current game state (hand, position, stack sizes, pot, prior actions), optional outputs from Modules 1-3 (rule constraints, search recommendations, Monte Carlo confidence intervals), and structured prompt templates for decision guidance.

**Output:** Action recommendation (fold/call/raise with size), natural-language reasoning trace, and confidence score. Output format: dictionary with selected action, bet size, explanation, and optional references to supporting signals from earlier modules.

**Integration:** This module converts structured game context into an LLM prompt and uses model output to produce a playable decision. It can optionally incorporate Module 1 constraints and Module 2/3 recommendations as context, but remains a distinct decision-making agent focused on language-model reasoning.

**Agent Usage:** Used by **Agent 3 (LLM Agent)** to make context-aware decisions with explainable reasoning.

**Prerequisites:** Course content on language models, prompt design, and model evaluation. Modules 1-3 (optional) for structured context features.

---

### Module 5: Adaptive Opponent Exploitation

**Topics:** Reinforcement Learning (MDP, Policy, Value Functions, Q-Learning)

**Input:** Historical game data (list of tuples: (hand, position, action_taken, opponent_action, outcome, reward)), opponent tendency category (string), and optional baseline strategies from Modules 1-3 and Module 4.

**Output:** Learned policy (dictionary mapping (hand, position, opponent_tendency) to optimal action with Q-values), exploitation strategy recommendations, and updated action-value estimates (Q-table or function approximation).

**Integration:** This module trains an RL policy to adapt decisions based on outcomes and opponent behavior over time. It can be initialized from other module recommendations but ultimately learns from interaction data to improve performance.

**Agent Usage:** Used by **Agent 4 (Adaptive Learning Agent)** to make decisions that adapt and exploit opponent behavior.

**Prerequisites:** Course content on Reinforcement Learning, MDPs, Q-Learning, and policy learning. Modules 1, 3, and 4 (optional) for initialization and comparison baselines.

---

## The Four AI Agents

### Agent 1: Rule-Based + Search Agent
**Modules Used:** Module 1 (Propositional Logic) + Module 2 (A* Search)

**Strategy:**
1. Uses Module 1 to determine if hand is playable (CNF rules, backward chaining)
2. If playable, uses Module 2 (A* search) to find optimal bet size
3. Combines rule-based constraints with heuristic search

**Strengths:**
- Transparent reasoning (can show exact rules and search process)
- Fast decision-making
- Good for educational purposes

**Weaknesses:**
- Limited by fixed rules
- May not adapt to opponent behavior

---

### Agent 2: Monte Carlo Agent
**Modules Used:** Module 3 (Monte Carlo Simulation)

**Strategy:**
1. Uses Monte Carlo simulation to estimate EV for different actions
2. Runs many trials to find optimal opening actions
3. No heuristics - pure simulation-based

**Strengths:**
- More accurate EV estimates through simulation
- Can handle complex scenarios
- Provides confidence intervals

**Weaknesses:**
- Slower (requires many simulations)
- Computationally intensive

---

### Agent 3: LLM Strategy Agent
**Modules Used:** Module 4 (LLM-Based Strategy Agent)

**Strategy:**
1. Builds a structured prompt from the game state
2. Uses an LLM to choose fold/call/raise and sizing
3. Returns both an action and reasoning/explanation

**Strengths:**
- Flexible reasoning over varied scenarios
- Human-readable explanations
- Easy to extend with prompt/tool improvements

**Weaknesses:**
- Output quality depends on prompt/model quality
- Can be inconsistent without strict constraints
- May need guardrails for reliable bet sizing

---

### Agent 4: Adaptive Learning Agent
**Modules Used:** Module 5 (Reinforcement Learning)

**Strategy:**
1. Learns from game history
2. Adapts strategy based on opponent behavior
3. Uses Q-learning to update policy

**Strengths:**
- Adapts to opponent tendencies
- Can exploit weaknesses
- Improves over time

**Weaknesses:**
- Requires training data
- May overfit to specific opponents

---

## System Features

### User vs. Agent Competition
- Users can select which agent to play against
- Real-time gameplay with AI decision visualization
- See reasoning from each agent's underlying modules
- Track performance against different agents

### Agent vs. Agent Competition
- Automated tournaments between agents
- Round-robin and elimination formats
- Quantitative performance metrics:
  - Win rates
  - Expected value achieved
  - Decision quality
  - Speed of decision-making
- Head-to-head statistics showing which agent beats which

### Comparative Analysis
- Performance dashboards showing agent rankings
- Matchup matrices (win rates for each pairing)
- Analysis of when each agent performs best
- Educational insights into trade-offs between approaches

---

## Feasibility Study

_A timeline showing that each module's prerequisites align with the course schedule._

| Module | Required Topic(s) | Topic Covered By | Checkpoint Due | Agent Implementation |
| ------ | ----------------- | ---------------- | -------------- | -------------------- |
| 1      | Propositional Logic | Week 2 | Wednesday, Feb 11  | Agent 1 (partial) |
| 2      | Informed Search (A*), Optimization | Week 3 | Thursday, Feb 26 | Agent 1 (complete) |
| 3      | Monte Carlo, Optimization | Week 5.5 | Thursday, March 19 | Agent 2 (complete) |
| 4      | LLM Agent Design & Prompt Engineering | Week 7 | Thursday, April 2 | Agent 3 (complete) |
| 5      | Reinforcement Learning | Week 10 | Thursday, April 16 | Agent 4 (complete) |

**Agent Development Timeline:**
- **Checkpoint 2**: Agent 1 fully functional (Modules 1 + 2)
- **Checkpoint 3**: Agents 1 + 2 functional (Modules 1-3)
- **Checkpoint 4**: Agents 1-3 functional (Modules 1-4)
- **Checkpoint 5**: All 4 agents functional (Modules 1-5) + comparison system

---

## Coverage Rationale

This topic selection fits poker strategy analysis naturally and enables meaningful comparison of AI techniques. **Propositional Logic** encodes fundamental decision rules that establish the knowledge foundation. **Informed Search (A*)** finds optimal bet sizes by exploring action spaces efficiently using heuristics. **Monte Carlo Methods** provide an alternative approach through simulation, demonstrating how different optimization techniques compare. **LLM-based reasoning** provides a flexible strategy agent with explainable natural-language outputs. **Reinforcement Learning** enables adaptive exploitation, showing how learning-based approaches can outperform static strategies.

The progression from rules → search → simulation → LLM reasoning → learning demonstrates how different AI paradigms complement each other. Each topic addresses a distinct aspect: logic provides structure, search finds solutions, simulation estimates values, LLMs provide contextual reasoning, and RL enables adaptation.

**Comparative Value:** By implementing each technique as a playable agent, the system enables direct quantitative comparison:
- Which approach wins more often?
- Which has higher expected value?
- Which adapts better to opponents?
- What are the trade-offs (speed vs. accuracy, exploitation vs. unexploitability)?

This comparative analysis provides unique educational and research value, demonstrating not just that each technique works, but how they compare in practice.

**Trade-offs considered:** 
- Supervised Learning could predict opponent actions but was omitted to focus on strategic optimization
- First-Order Logic could encode more complex relationships but Propositional Logic suffices for pre-flop rules
- For LLM-based decisions, output quality depends on prompt design and guardrails; the system mitigates this with structured prompts and action validation
- The focus on pre-flop (rather than full game trees) makes the system feasible while still demonstrating all required concepts effectively
- Agent comparison adds minimal complexity (standardized interface) while providing significant value

---

## Technical Architecture

### Agent Interface
All agents implement a standardized interface:
```python
class PokerAgent:
    def make_decision(
        hand: str,
        position: str,
        stack_sizes: Tuple[int, int],
        pot: float,
        current_bet: float,
        action_history: List[str],
        opponent_tendency: str = "Unknown"
    ) -> Dict:
        """
        Returns:
        {
            'action': 'fold' | 'call' | 'raise',
            'bet_size': float,
            'ev': float,
            'reasoning': str,
            'module_info': dict  # Agent-specific information
        }
        """
```

### System Components
1. **Module Implementations**: Core AI logic (Modules 1-5)
2. **Agent Wrappers**: Standardized interfaces around modules
3. **Game Engine**: Manages gameplay, state, and rules
4. **Frontend**: Web interface for user interaction
5. **Competition System**: Automated agent vs. agent matches
6. **Analytics**: Performance tracking and comparison

---

## Expected Outcomes

### Quantitative Results
- Win rates for each agent
- Expected value comparisons
- Head-to-head matchup statistics
- Performance by stack depth and position

### Educational Insights
- Demonstration of trade-offs between AI techniques
- When each approach performs best
- How different paradigms complement each other
- Practical lessons for AI strategy design

### Research Value
- Publishable comparison of AI techniques
- Quantitative analysis of approach effectiveness
- Insights into poker strategy optimization
- Demonstration of multi-paradigm AI systems

---

## Deliverables

1. **Five AI Modules**: Complete implementations of Modules 1-5
2. **Four AI Agents**: Playable agents wrapping the modules
3. **Web Frontend**: User interface for playing against agents
4. **Competition System**: Agent vs. agent tournament framework
5. **Comparative Analysis**: Performance metrics and insights
6. **Documentation**: Module specs, agent descriptions, comparison results
7. **Tests**: Unit tests for modules, integration tests for agents, competition tests

---

## Success Criteria

- ✅ All 5 modules implemented and tested
- ✅ All 4 agents functional and playable
- ✅ Users can compete against any agent
- ✅ Agents can compete against each other
- ✅ Quantitative comparison data collected
- ✅ Clear insights into trade-offs between approaches
- ✅ System demonstrates understanding of all AI topics

---

This proposal maintains all original course requirements while adding significant value through comparative analysis and interactive agent competition. The agent-based organization makes the system more engaging, educational, and research-worthy while still demonstrating mastery of all required AI concepts.
