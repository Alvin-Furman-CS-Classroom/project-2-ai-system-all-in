# Plan: Preflop-Strategy Agents + Full-Board Showdown

This document describes a **game layer** that keeps **all agent intelligence pre-flop** while still supporting **head-to-head matches**, **user play**, and a satisfying “full hand” experience. Post-flop **betting** is intentionally omitted; the board exists for **resolution and display** only.

---

## 1. Goals

| Goal | Description |
|------|-------------|
| **G1** | Agents (Modules 1–2, 3, 4, 5 wired as policies) compete in **simulated HU hands** with comparable rules. |
| **G2** | Produce **statistics** (win rates, chips, optional pre-flop stats like fold frequency / open sizing) over many hands. |
| **G3** | Allow a **human** to play against each agent with clear feedback. |
| **G4** | Preserve the **course scope**: strategic content remains **pre-flop only**; no requirement for GTO or RL on the flop. |

---

## 2. Scope

### In scope

- **Heads-up** Texas Hold’em, **one table**, **fixed or configurable** starting stacks (in BB).
- **Pre-flop action round** only: legal actions depend on position and facing action (e.g. fold, open to X BB, possibly call/fold to an open—exact menu to match your pre-flop module APIs).
- After pre-flop betting **ends** (everyone folded except one, or **both players are committed** to seeing a showdown):
  - **Deal the full board** (5 community cards) from a **single shuffled 52-card deck** with no card reuse.
  - **Evaluate** best 5-card hand from 7 cards per player.
  - **Award the pot** (including fold wins without a runout when applicable).

### Out of scope (unless explicitly added later)

- **Post-flop betting** (flop, turn, river action).
- **Multi-way** pots (3+ players).
- **Tournament ICM** (payout pressure); optional future extension.
- **Solver-grade** post-flop play from any agent.

### Clarification for reports and demos

> *Agents decide only pre-flop. The flop, turn, and river are dealt only to determine the winner at showdown when both players remain; there is no strategic play on later streets.*

---

## 3. High-level architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Game engine (new)                        │
│  State machine: blinds → pre-flop → (fold ends) or showdown  │
│  Deck, pot, stacks, board, terminal payoffs                  │
└───────────────────────────┬─────────────────────────────────┘
                            │ legal actions + state
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
   Agent A            Agent B              Human UI
 (Module policies)  (Module policies)    (same API as agents)
```

- **Engine** is the **single source of truth** for rules and chip movement.
- Each **agent** implements a small interface, e.g. `choose_action(state) -> action`, where `state` is pre-flop-only (or includes “facing open” flags). No agent reads the board for **decisions**.

---

## 4. Components to build

### 4.1 Game state and rules

- **Positions**: Button / Small Blind / Big Blind in HU (often BTN posts SB, BB posts BB; confirm one convention and stick to it).
- **Stacks, pot, current bet to call**, **whose turn**, **street** (always `preflop` until terminal or showdown branch).
- **Terminal conditions**:
  - **Fold**: other player wins pot; no board.
  - **Showdown path**: both in—advance to **runout** (see below).

### 4.2 Deck and runout

- **Shuffle** 52 cards; deal **2 hole cards** to each player; **burn** optional for realism (can skip if documented).
- When entering showdown:
  - Deal **5 board cards** (either all at once or flop + turn + river with **no** betting between—purely cosmetic).
- Ensure **no duplicate** cards (common bug if hole and board share a deck incorrectly).

### 4.3 Hand evaluation

- Implement or adopt a **7-card evaluator** (best 5 of 7) with standard Hold’em hand rankings.
- Unit tests: known examples (flush vs full house, kicker issues, wheel straight, split pots).

### 4.4 Agent adapter layer

Map each paradigm to the same interface:

| Agent | Source | Pre-flop decision |
|-------|--------|-------------------|
| 1 | Modules 1–2 | Rules + search for open / fold (per your APIs) |
| 2 | Module 3 | Monte Carlo opening optimization or cached policy |
| 3 | Module 4 | Nash / reference frequencies → sample or argmax |
| 4 | Module 5 | Q-table or policy from learned data |

**Important:** adapters may **precompute** a range table at session start for speed; the engine still only asks for an action for the **current** state.

### 4.5 Match runner and statistics

- **Session**: N hands, same rules, optional seat swap (BTN alternates in HU).
- **Per matchup** (e.g. Agent 2 vs Agent 3): record wins, chips won/lost, hands played.
- **Derived metrics**: BB/100 over session, fold %, open frequency, average open size (all from pre-flop logs).
- Optional: **confidence intervals** on win rate (binomial) or on mean chips per hand.

### 4.6 Human player

- Same engine; human chooses from **legal** actions in the UI or CLI.
- Optional “trainer” panel: after the hand, show what each agent would have done (compare policies).

---

## 5. Phased implementation plan

### Phase A — Engine core (minimum playable)

1. Represent state + legal pre-flop actions (even if action set is small at first).
2. Deck + hole cards + fold handling + pot to winner.
3. If both live: runout + evaluator + split pot logic.

**Exit criterion:** two **random** legal agents can play N hands without crashes; chips conserve except rake (if any).

### Phase B — One real agent

1. Wire **one** module-backed agent (e.g. Module 3) through the adapter.
2. Play vs random and vs copy of itself; sanity-check stats.

### Phase C — Full roster + stats

1. Wire remaining agents (or stubs with fixed policies first).
2. **Round-robin** or matrix of matchups; export CSV or simple dashboard.

### Phase D — UX

1. CLI or web UI for human play and for viewing matchup results.
2. Optional: animate board runout for showdown (no strategic effect).

---

## 6. Risks and mitigations

| Risk | Mitigation |
|------|------------|
| Hand evaluator bugs | Property tests + reference cases; compare to known library if allowed. |
| Scope creep (post-flop betting) | Keep a checklist; reject betting features in engine PRs until scope changes. |
| Slow Monte Carlo per action | Cache policies, reduce trials in real-time play, or separate “analysis mode” vs “play mode”. |
| Inconsistent HU blind rules | Document one scheme; test odd-stack edge cases. |

---

## 7. Documentation and course alignment

- Update **README / AGENTS** when this layer exists: “**Strategic agents are pre-flop-only; the engine runs out boards for showdown resolution.**”
- Checkpoint reports can cite: **game engine + adapters** as integration work, distinct from **Module 3** Monte Carlo internals.

---

## 8. Open decisions (fill in as a team)

- [x] **UI:** Web (Flask). **Limp** allowed (call to match BB; BB may check or raise afterward).
- [x] **Starting stacks** default 2000 chips; SB = 10, BB = 20 (1 BB = 20 chips).
- [ ] Exact **raise ladder** (currently: min raise plus 3–6 BB total options where affordable).
- [ ] Whether **show board on fold** (usually no) or **muck** rules for UI only.
- [x] **Seating:** button alternates each new hand in the web session.

### Run the web demo

From project root (after `pip install -r requirements.txt`):

```bash
python3 -m web_app.server
```

Open `http://127.0.0.1:5000/`. Seat 0 is you (BTN/SB); seat 1 is a **random legal** bot. No post-flop betting—showdown runs out five cards after pre-flop ends.

---

## 9. Summary

This plan delivers an **interesting final product**—real matches, real stats, human play, and visual runouts—while keeping **all module-based strategy pre-flop**. The main engineering cost is a **correct engine** (deck + evaluator + pot logic), not post-flop AI. Everything else is **integration and presentation**.
