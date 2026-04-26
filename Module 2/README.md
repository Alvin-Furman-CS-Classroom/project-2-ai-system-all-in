# Module 2: Full-Hand Fast Heuristic Search

Module 2 now supports full-hand decisioning (`preflop`, `flop`, `turn`, `river`) using a lightweight A*/brute-force EV search with deterministic heuristics.

## What changed

- **Street-aware search context** in `bet_sizing_search.py` via `full_hand_context`.
- **Fast postflop heuristic EV** in `ev_calculator.py`:
  - street multipliers,
  - board-texture adjustments (`paired`, `flush_draw`, `wet`),
  - SPR-aware pressure adjustments.
- **Street-specific bet candidates** in `bet_size_discretization.py`:
  - preflop BB-multiple candidates,
  - postflop pot-fraction candidates.

## Main API

Use the existing entrypoint and pass `full_hand_context` for full-hand spots:

```python
from bet_sizing_search import optimal_bet_sizing_search

result = optimal_bet_sizing_search(
    hand="AKs",
    position="Button",
    stack_sizes=(60, 60),  # hero, villain in BB
    opponent_tendency="Unknown",
    use_module1=False,
    full_hand_context={
        "hand": "AKs",
        "position": "Button",
        "stack_sizes": (60, 60),
        "opponent_tendency": "Unknown",
        "street": "flop",
        "pot_size": 8.0,  # BB
        "opponent_bet_size": 2.5,  # BB faced by hero, or None if unopened
        "board_features": {"paired": False, "flush_draw": True, "wet": True},
    },
)
```

Returned fields include:

- `action` (`fold`, `call`, `raise`, `open`)
- `bet_size` (BB units)
- `expected_value`
- `street`

## Full web app integration

In the full-game engine, Module 2 is exposed as bot id `m2`:

- `full_game_engine/bot_agents.py` maps engine state -> Module 2 context.
- `full_game_web_app/templates/index.html` provides a selectable `m2` opponent option.

## Limitations

- This is **heuristic**, not game-theoretic solving.
- No full tree rollouts or exact postflop equity simulation.
- Opponent tendency remains a simplified category model.

