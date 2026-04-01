# Module 4: LLM Strategic Advisor (Ollama / Llama 3.2)

**Approved pivot (per instructor):** Module 4 no longer centers on Nash/GTO chart lookup. It uses a **large language model** to recommend actions from a structured description of the situation, with **validation** against legal engine actions and optional comparison to Modules 2–3.

**Topics to highlight in write-ups:** prompt engineering, structured generation, API integration, failure modes and guardrails, evaluation vs rule-based and simulation agents.

---

## Purpose

Given a **natural-language or JSON-style game snapshot** (hole cards, position, stacks, pot, legal actions, optional opponent label), the module asks an LLM: *what is the best play among the legal options?* and returns a **machine-usable action** plus optional **rationale** (for UI or reports).

This is **Agent 3** in the UI narrative (LLM advisor), distinct from Agent 1 (logic + search) and Agent 2 (Monte Carlo).

---

## Inputs (target contract)

| Field | Description |
| ----- | ----------- |
| `hand` | Compact hand string (e.g. `AKs`, `72o`) or card list |
| `position` | `Button` or `Big Blind` |
| `stack_hero_bb`, `stack_villain_bb` | Floats in big blinds |
| `pot_bb` | Pot size in BB (or chips + `bb_chips`) |
| `to_call_chips` | Chips to call, if any |
| `legal_actions` | List of dicts matching `game_engine.hu_preflop` legal actions |
| `opponent_tendency` | Optional: `Tight`, `Loose`, etc. |
| `history_summary` | Optional short text of recent actions |

---

## Outputs (target contract)

| Field | Description |
| ----- | ----------- |
| `action` | One legal action dict (e.g. `{"kind":"fold"}`, `{"kind":"raise_to","total":60}`) |
| `raw_model_text` | Optional: model explanation (for display only) |
| `meta` | Model id, latency, whether response was repaired after validation |

---

## Environment Variables

```bash
# Ollama
OLLAMA_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.2
OLLAMA_TIMEOUT_S=10
```

---

## Architecture (high level)

```
game state + legal_actions
        │
        ▼
  build_prompt()  ──►  Ollama llama3.2  ──►  parse JSON/plain text
        │                      │
        │                      ▼
        │              validate_against_legal()
        │                      │
        │              on failure: retry with stricter index instruction
        │              then engine fallback (random legal)
        ▼
  { action, raw_text?, meta }
```

---

## Guardrails (required for a defensible module)

1. **Structured output:** Instruct the model to return **only JSON** matching a schema you put in the prompt (or use API **JSON mode / response schema** if available for your SDK version).
2. **Validate:** Map parsed output to `legal_actions` from the engine; if not a match, **repair or reject**.
3. **Timeouts:** Cap request time; on timeout, use fallback policy (document which).
4. **No key in repo:** CI and teammates use env vars; never commit secrets.
5. **Tests:** Unit tests use **mocked HTTP/SDK** or a recorded fixture string—**no live API in default test runs.**

---

## Implementation phases (suggested order)

| Phase | Task |
| ----- | ---- |
| **1** | Add dotenv support; create `llm_policy.py` with `choose_action(state_dict, legal_actions) -> dict`. |
| **2** | Implement `build_system_prompt` + `build_user_prompt` from a frozen template; document prompts in this README or `prompts/`. |
| **3** | JSON parse + validate + single retry on invalid output. |
| **4** | `demo_module4.py` CLI: read a JSON file or stdin, print chosen action + explanation. |
| **5** | `unit_tests/Module 4/test_llm_policy.py` with mocks for parsing and provider fallback paths. |
| **6** | Integrate into `game_engine/bot_agents.py` as agent id e.g. `m4` or `llm`; add dropdown + `/api/set_agent` in `web_app`. |
| **7** | Short evaluation note: win rate or EV vs random / Agent 1 / Agent 2 over N simulated or logged hands. |

---

## Files

| File | Role |
| ---- | ---- |
| `llm_policy.py` | Snapshot builder, index-based choice, parser/validation, Ollama client integration. |
| `prompts.py` | System + user prompts (enumerated legal actions). |
| `demo_module4.py` | Live demo (requires local Ollama running). |
| `.env.example` | Documents Ollama environment variables. |

---

## Dependencies on other modules

- **None required** for LLM core policy selection beyond prompt + legal list.
- **Optional:** compare LLM picks to Module 2 / Module 3 outputs in analysis or tests.
- **Module 5** can later use Module 4 as a **baseline policy** or alternate prior (per your updated system design).

---

## Checkpoint / grading angle

Emphasize:

- Clear **inputs/outputs** and **reproducibility** where possible (temperature 0, logged prompts).
- **Responsible use:** validation layer, no silent illegal plays.
- **Comparison** to symbolic (Module 1–2) and sampling (Module 3) agents.

---

## References

- [Ollama API documentation](https://github.com/ollama/ollama/blob/main/docs/api.md)
