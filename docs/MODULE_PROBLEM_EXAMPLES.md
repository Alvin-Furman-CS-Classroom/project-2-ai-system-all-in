# Problems Solved by Each Module

This document provides concrete examples of problems the system can solve upon completion of each module.

---

## Module 1: Rule-Based Decision Framework
**Topic:** Propositional Logic (Knowledge Bases, Inference Methods, Chaining, CNF)

### Problems Solved:

#### Problem 1: "Should I play this hand from this position?"
**Scenario:** You have **K9s** (King-9 suited) on the **Button** with **30 big blinds** against a **Loose** opponent.

**Solution:** Module 1 evaluates:
- Position: Button (advantage) ✓
- Hand strength: Top 50% (K9s is ~40th percentile) ✓
- Stack size: 30 BB (adequate, >20 BB) ✓
- Opponent: Loose (allows wider range) ✓

**Output:** `playable = True` with reasoning: "Medium strength hand on Button with adequate stack. Hand is playable against Loose opponent due to position advantage."

#### Problem 2: "Is this hand too weak to play?"
**Scenario:** You have **72o** (7-2 offsuit, worst hand) in the **Big Blind** with **15 big blinds** against an **Aggressive** opponent.

**Solution:** Module 1 applies rules:
- Position: Big Blind (out of position) ✗
- Hand strength: Bottom 50% (worst hand) ✗
- Stack size: 15 BB (inadequate, <20 BB) ✗

**Output:** `playable = False` with reasoning: "Weak hand from Big Blind position with short stack. Hand is not playable."

#### Problem 3: "Should I play premium hands even with a short stack?"
**Scenario:** You have **AA** (pocket Aces, best hand) on the **Button** with only **10 big blinds** against an **Unknown** opponent.

**Solution:** Module 1 applies exception rule:
- Hand strength: Top 5% (premium exception) ✓
- Stack size: 10 BB (short, but exception applies) ✓

**Output:** `playable = True` with reasoning: "Premium hand (AA) is always playable even with short stack. Exception rule applies for top 5% hands."

#### Problem 4: "What rules govern my decision-making?"
**Scenario:** You want to understand the logical framework behind poker decisions.

**Solution:** Module 1 provides the complete knowledge base in CNF format:
- All rules encoded as propositional logic
- Inference chain showing how facts lead to conclusions
- Queryable knowledge base for decision support

**Output:** Structured knowledge base with CNF rules, facts, and inference trace.

---

## Module 2: Optimal Bet Sizing Search
**Topic:** Informed Search (A*, IDA*, Beam Search), Optimization

### Problems Solved:

#### Problem 1: "What's the optimal bet size for this hand?"
**Scenario:** You have **AKs** (Ace-King suited) on the **Button** with **50 big blinds** each, against a **Tight** opponent. Module 1 says it's playable.

**Solution:** Module 2 searches bet sizes (1x, 2x, 2.5x, 3x, 4x, 5x BB) using A* search:
- Evaluates expected value for each bet size
- Considers opponent fold/call/raise probabilities (Tight opponent: 40% fold, 50% call, 10% raise)
- Uses hand equity (AKs has ~66% equity heads-up)
- Finds optimal: **3x big blind raise** with EV = +2.1 BB

**Output:** `optimal_bet_size = 3.0`, `action = "raise to 3x BB"`, `expected_value = 2.1 BB`

#### Problem 2: "Should I fold, call, or raise with this marginal hand?"
**Scenario:** You have **K9s** on the **Button** with **30 big blinds** against a **Loose** opponent. Module 1 says playable.

**Solution:** Module 2 searches all actions:
- **Fold:** EV = 0 BB (no risk, no reward)
- **Call:** EV = -0.3 BB (negative due to position disadvantage)
- **Raise 2x:** EV = +0.8 BB (profitable due to fold equity)
- **Raise 3x:** EV = +0.5 BB (less profitable, more risk)

**Output:** `optimal_bet_size = 2.0`, `action = "raise to 2x BB"`, `expected_value = 0.8 BB`

#### Problem 3: "What's the best bet size against an aggressive opponent?"
**Scenario:** You have **QQ** (pocket Queens) on the **Button** with **40 big blinds** against an **Aggressive** opponent who 3-bets frequently.

**Solution:** Module 2 adjusts for aggressive opponent (30% fold, 40% call, 30% raise):
- Smaller raises get more calls (bad for QQ)
- Larger raises get more folds (good)
- Optimal: **4x big blind raise** to maximize fold equity

**Output:** `optimal_bet_size = 4.0`, `action = "raise to 4x BB"`, `expected_value = 3.2 BB`

#### Problem 4: "How does stack size affect bet sizing?"
**Scenario:** You have **AKo** with **10 big blinds** (short stack) vs **100 big blinds** (deep stack).

**Solution:** Module 2 considers stack-to-pot ratios:
- **Short stack (10 BB):** Optimal = **All-in** (push/fold strategy)
- **Deep stack (100 BB):** Optimal = **3x BB raise** (standard sizing)

**Output:** Short stack: `action = "all-in"`, Deep stack: `action = "raise to 3x BB"`

---

## Module 3: Opening Range Optimization
**Topic:** Advanced Search (Hill Climbing, Simulated Annealing, Genetic Algorithms), Optimization

### Problems Solved:

#### Problem 1: "What hands should I play from the Button?"
**Scenario:** You're on the **Button** with **50 big blinds** against a **Loose** opponent. You want to know your optimal opening range.

**Solution:** Module 3 uses Genetic Algorithm to optimize:
- Starts with Module 2's bet sizing recommendations
- Evolves hand combinations to maximize overall range EV
- Considers position advantage, opponent tendencies, stack depth

**Output:** 
- `optimal_range_percentage = 0.65` (top 65% of hands)
- `optimal_hands = ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22", "AKs", "AKo", "AQs", "AQo", "AJs", "AJo", "ATs", "ATo", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s", "KQs", "KQo", "KJs", "KJo", "KTs", "KTo", "K9s", "QJs", "QJo", "QTs", "QTo", "Q9s", "JTs", "JTo", "J9s", "T9s", "T8s", "98s", "97s", "87s", "86s", "76s", "75s", "65s", "64s", "54s", "53s", "43s", "32s"]`
- `range_expected_value = 1.8 BB per hand`

#### Problem 2: "How tight should I play from the Big Blind?"
**Scenario:** You're in the **Big Blind** with **30 big blinds** against a **Tight** opponent.

**Solution:** Module 3 optimizes defensive range:
- Considers pot odds (already invested 1 BB)
- Uses Simulated Annealing to find optimal defense range
- Balances between folding too much (exploitable) and calling too much (losing money)

**Output:**
- `optimal_range_percentage = 0.55` (top 55% of hands for defense)
- `optimal_hands = [list of 93 hands]`
- `range_expected_value = -0.2 BB per hand` (slight loss expected, but better than folding everything)

#### Problem 3: "What's my optimal range against different opponent types?"
**Scenario:** Compare optimal ranges against **Tight**, **Loose**, **Aggressive**, and **Passive** opponents from Button.

**Solution:** Module 3 optimizes separately for each opponent type:
- **Against Tight:** Range = 45% (tighter, exploit their tightness)
- **Against Loose:** Range = 70% (wider, value bet more)
- **Against Aggressive:** Range = 50% (medium, avoid getting 3-bet too often)
- **Against Passive:** Range = 75% (very wide, exploit their passivity)

**Output:** Four optimized ranges with different hand lists and EV calculations.

#### Problem 4: "How does stack size affect my opening range?"
**Scenario:** Compare Button opening ranges with **10 BB**, **30 BB**, and **100 BB** stacks.

**Solution:** Module 3 optimizes for each stack depth:
- **10 BB (ultra-short):** Range = 50% (push/fold, wider than normal)
- **30 BB (short):** Range = 40% (tighter, avoid marginal spots)
- **100 BB (deep):** Range = 65% (wider, post-flop playability matters)

**Output:** Three optimized ranges showing how stack depth affects strategy.

---

## Module 4: Nash Equilibrium Strategy Analysis
**Topic:** Games and Game Theory (Minimax, Nash Equilibrium, Mixed Strategies)

### Problems Solved:

#### Problem 1: "How close is my strategy to optimal play?"
**Scenario:** You've optimized your Button opening range to 60% of hands with 3x BB raises. How does this compare to Nash equilibrium?

**Solution:** Module 4 compares your strategy to known heads-up pre-flop Nash equilibrium:
- **Your range:** 60% of hands
- **Nash equilibrium range:** 65% of hands
- **Deviation:** -5 percentage points (slightly tighter than optimal)

**Output:**
```python
{
    "deviation_metrics": {
        "range_deviation": -0.05,  # 5% tighter
        "bet_size_deviation": 0.0,  # Same as equilibrium
        "overall_deviation_score": 0.12  # Low deviation (good)
    },
    "exploitability": 0.8,  # BB per 100 hands (low, good)
    "equilibrium_reference": {
        "button_range": 0.65,
        "button_bet_size": 3.0,
        "bb_defense_range": 0.60
    }
}
```

#### Problem 2: "How exploitable is my strategy?"
**Scenario:** Your optimized strategy plays 70% of hands from Button. Is this exploitable?

**Solution:** Module 4 analyzes exploitability:
- Computes how an optimal opponent would exploit your strategy
- Finds that playing 70% is too wide against optimal play
- Calculates exploitability: **2.5 BB per 100 hands**

**Output:**
```python
{
    "exploitability": 2.5,  # BB per 100 hands (moderate)
    "exploitation_method": "Opponent should 3-bet wider (25% instead of 15%)",
    "recommendation": "Tighten range to 60-65% to reduce exploitability"
}
```

#### Problem 3: "What's the theoretical baseline for this situation?"
**Scenario:** You want to know the Nash equilibrium strategy for Button vs Big Blind with 50 BB stacks.

**Solution:** Module 4 provides equilibrium reference data:
- Button opening range: 65% of hands
- Button bet sizing: 3x BB (mixed: 80% 3x, 20% 2.5x)
- Big Blind defense: 60% of hands
- Big Blind 3-bet frequency: 15%

**Output:** Complete equilibrium strategy with mixed strategy frequencies.

#### Problem 4: "Should I deviate from equilibrium to exploit my opponent?"
**Scenario:** Your opponent is very tight (only plays 30% of hands). Should you deviate from Nash equilibrium?

**Solution:** Module 4 identifies profitable deviations:
- **Equilibrium:** Play 65% of hands
- **Exploitative:** Play 75% of hands (wider to exploit their tightness)
- **Expected gain:** +1.2 BB per 100 hands by deviating

**Output:**
```python
{
    "equilibrium_strategy": {"range": 0.65},
    "exploitative_strategy": {"range": 0.75},
    "expected_gain": 1.2,  # BB per 100 hands
    "recommendation": "Deviate to wider range to exploit tight opponent"
}
```

---

## Module 5: Adaptive Opponent Exploitation
**Topic:** Reinforcement Learning (MDP, Policy, Value Functions, Q-Learning)

### Problems Solved:

#### Problem 1: "How should I adapt to this specific opponent?"
**Scenario:** You've played 100 hands against an opponent. Historical data shows:
- They fold to 70% of your raises (very tight)
- They only 3-bet with premium hands (AA, KK, QQ, AK)
- They call too often with weak hands

**Solution:** Module 5 uses Q-Learning to adapt:
- Learns that this opponent is exploitable by betting wider
- Adjusts strategy: Play 75% of hands (wider than equilibrium 65%)
- Increases bet sizing to 3.5x BB (they fold too much)

**Output:**
```python
{
    "learned_policy": {
        ("AKs", "Button", "Tight"): {"action": "raise", "bet_size": 3.5, "q_value": 2.8},
        ("K9s", "Button", "Tight"): {"action": "raise", "bet_size": 3.0, "q_value": 1.2},
        # ... more hand/position combinations
    },
    "exploitation_recommendations": {
        "range_adjustment": "+10%",  # Play 10% wider
        "bet_size_adjustment": "+0.5x",  # Increase bet size
        "expected_gain": 3.5  # BB per 100 hands
    }
}
```

#### Problem 2: "What have I learned about this opponent's tendencies?"
**Scenario:** After 500 hands, you want to see what the system has learned.

**Solution:** Module 5 provides learned Q-values and policy:
- Q-values show expected rewards for each action
- Policy shows optimal actions for each situation
- Identifies opponent patterns: "Folds to 3-bets 85% of the time"

**Output:**
```python
{
    "opponent_profile": {
        "fold_frequency": 0.85,  # Very high
        "3bet_frequency": 0.08,  # Very low
        "call_frequency": 0.07,
        "tendency_category": "Extremely Tight"
    },
    "learned_exploits": [
        "Bet wider range (exploit high fold frequency)",
        "3-bet more frequently (they fold too much)",
        "Value bet thinner (they call with weak hands)"
    ]
}
```

#### Problem 3: "How should my strategy evolve as I learn more?"
**Scenario:** You've played 50 hands, then 200 hands, then 500 hands. How does strategy change?

**Solution:** Module 5 shows policy evolution:
- **After 50 hands:** Still using equilibrium strategy (not enough data)
- **After 200 hands:** Starting to exploit (play 68% of hands, slight deviation)
- **After 500 hands:** Fully exploitative (play 78% of hands, significant deviation)

**Output:** Policy evolution showing how Q-values and recommendations change with more data.

#### Problem 4: "What's the optimal action for this specific situation?"
**Scenario:** You have **K9s** on the **Button** against an opponent you've played 300 hands with. What should you do?

**Solution:** Module 5 uses learned Q-values:
- Q(raise 3x) = 1.2 BB
- Q(raise 2.5x) = 0.9 BB
- Q(fold) = 0 BB
- Q(call) = -0.3 BB

**Output:** `optimal_action = "raise to 3x BB"`, `q_value = 1.2 BB`, `confidence = 0.85`

---

## Complete System Integration

### Problem: "Give me the optimal strategy for this entire session"
**Scenario:** You're playing heads-up poker. You want a complete strategy recommendation.

**Solution:** All modules work together:
1. **Module 1:** Determines which hands are fundamentally playable
2. **Module 2:** Finds optimal bet sizes for each playable hand
3. **Module 3:** Optimizes your overall opening range
4. **Module 4:** Compares to Nash equilibrium, identifies deviations
5. **Module 5:** Adapts strategy based on opponent behavior

**Output:** Complete integrated strategy with:
- Opening ranges for each position
- Bet sizing recommendations
- Exploitation adjustments
- Expected value calculations
- Confidence levels

---

## Summary Table

| Module | Key Problem Solved | Example Output |
|--------|-------------------|----------------|
| **Module 1** | "Is this hand playable?" | `playable = True/False` with reasoning |
| **Module 2** | "What's the optimal bet size?" | `raise to 3x BB, EV = 2.1 BB` |
| **Module 3** | "What's my optimal opening range?" | `65% of hands, EV = 1.8 BB/hand` |
| **Module 4** | "How close am I to optimal play?" | `5% deviation, 0.8 BB exploitability` |
| **Module 5** | "How should I exploit this opponent?" | `Play 10% wider, gain 3.5 BB/100` |
