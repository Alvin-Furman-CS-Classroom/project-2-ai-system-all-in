"""
Module 4 policy: choose an action by index via local Ollama (llama3.2).

Works with `game_engine.hu_preflop.HandState` (preflop-only) and
`full_game_engine.hu_hand.HandState` (all streets) when `street` / `board` exist.
"""

from __future__ import annotations

import json
import os
import random
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from prompts import SYSTEM_INSTRUCTION, build_user_prompt


def _load_dotenv_files() -> None:
    """Load ``.env`` from project root and ``Module 4/`` for local runtime config."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    m4_dir = Path(__file__).resolve().parent
    load_dotenv(m4_dir.parent / ".env")
    load_dotenv(m4_dir / ".env")


_load_dotenv_files()

DEFAULT_TIMEOUT_S = float(os.environ.get("OLLAMA_TIMEOUT_S", "15"))
MAX_OUTPUT_TOKENS = 256
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")


def hand_state_to_snapshot(
    state: Any,
    bot_seat: int,
    hand_str: str,
) -> Dict[str, Any]:
    """Build a JSON-serializable snapshot for the prompt (preflop-only or full-hand engine)."""
    bb = float(state.bb_chips)
    human = 1 - bot_seat
    pos = "Button" if state.button == bot_seat else "Big Blind"
    to_call = state.to_call(bot_seat)
    snap: Dict[str, Any] = {
        "phase": state.phase,
        "actor_seat": bot_seat,
        "opponent_seat": human,
        "position_hero": pos,
        "hero_hand": hand_str,
        "stacks_chips": [int(state.stacks[0]), int(state.stacks[1])],
        "stacks_bb": [round(state.stacks[0] / bb, 2), round(state.stacks[1] / bb, 2)],
        "pot_chips": int(state.pot),
        "pot_bb": round(state.pot / bb, 2),
        "bb_chips": int(state.bb_chips),
        "to_call_chips": int(to_call),
        "round_contrib_chips": [int(state.round_contrib[0]), int(state.round_contrib[1])],
    }
    street = getattr(state, "street", None)
    if street is not None:
        snap["street"] = str(street)
    board = getattr(state, "board", None)
    if board is not None:
        snap["board"] = [str(c) for c in board]
    return snap


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    if not text.startswith("```"):
        return text
    lines = text.split("\n")
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _parse_llm_json_blob(text: str) -> Dict[str, Any]:
    """Parse JSON from model output; tolerate markdown/prose/plain-text index formats."""
    text = _strip_code_fence(text)
    if not text:
        raise ValueError("model returned no JSON (empty after removing markdown fences)")
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        try:
            data = json.loads(text[start : end + 1])
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass

    # Last-resort parse: tolerate plain text like "option_index: 2\nreason: ...".
    m = re.search(r"option[_\s-]*index\s*[:=]\s*(-?\d+)", text, flags=re.IGNORECASE)
    if m:
        out: Dict[str, Any] = {"option_index": int(m.group(1))}
        mr = re.search(r"reason\s*[:=]\s*(.+)", text, flags=re.IGNORECASE | re.DOTALL)
        if mr:
            out["reason"] = mr.group(1).strip().strip('"')
        return out

    preview = text[:240].replace("\n", " ")
    raise ValueError(
        f"model output was not valid JSON (preview: {preview!r}…)"
    )


def _normalize_option_index(raw: Any, n_options: int) -> Optional[int]:
    """Map model output to a valid 0-based index; handle float / str / off-by-one last slot."""
    if n_options <= 0:
        return None
    try:
        if isinstance(raw, str) and raw.strip() != "":
            if raw.strip().lstrip("-").isdigit():
                idx = int(raw)
            else:
                idx = int(float(raw))
        else:
            idx = int(float(raw))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if 0 <= idx < n_options:
        return idx
    # Some models use 1..n for the n listed actions; shift when unambiguous.
    if 1 <= idx <= n_options:
        return idx - 1
    return None


def _friendly_api_error(e: BaseException) -> str:
    """Short, actionable copy for UI when Ollama returns common errors."""
    raw = str(e)
    if "Ollama unavailable" in raw:
        return raw
    if "not valid JSON" in raw or "JSONDecodeError" in raw:
        return "Ollama returned output that could not be parsed. Retry or use a different local model."
    if len(raw) > 480:
        return raw[:480] + "…"
    return raw


def _call_ollama(user_text: str, timeout_s: Optional[float] = None) -> Dict[str, Any]:
    """
    Fallback local call via Ollama.

    Expected response shape from model text:
    {"option_index": <int>, "reason": "..."}
    or plain text with option_index and reason lines.
    """
    strict_prompt = (
        user_text
        + "\n\nIMPORTANT (required): include BOTH option_index and reason. "
        + "Make reason detailed. Start with hero hand, pot size, and opponent action context; "
        + "then discuss hand strength/draws/board texture before the final action choice."
    )
    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "format": "json",
        "system": SYSTEM_INSTRUCTION,
        "prompt": strict_prompt,
        "options": {"temperature": 0},
    }
    req = urllib.request.Request(
        f"{OLLAMA_URL.rstrip('/')}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    t = max(1.0, float(timeout_s if timeout_s is not None else DEFAULT_TIMEOUT_S))
    try:
        with urllib.request.urlopen(req, timeout=t) as resp:
            body = resp.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as e:
        raise RuntimeError(
            f"Ollama unavailable at {OLLAMA_URL}. Ensure `ollama serve` is running."
        ) from e

    try:
        outer = json.loads(body)
    except json.JSONDecodeError as e:
        raise ValueError("Ollama returned non-JSON HTTP response") from e

    model_text = str(outer.get("response", "")).strip()
    if not model_text:
        raise ValueError("Ollama returned empty `response`")
    return _parse_llm_json_blob(model_text)


def _build_choice_prompt(base_prompt: str, attempt: int, max_idx: int) -> str:
    """Build attempt-specific prompt text for robust index extraction."""
    strict_extra = (
        "\n\nIMPORTANT: option_index must be an integer between 0 and "
        f"{max_idx} inclusive."
    )
    plain_text_hint = (
        "\n\nIf you cannot return strict JSON, plain text is acceptable in this exact format:\n"
        "option_index: <integer>\nreason: <short text>"
    )
    return base_prompt + (strict_extra if attempt == 1 else "") + plain_text_hint


def _extract_choice(data: Dict[str, Any], n_legal: int) -> Tuple[int, str]:
    """Extract and validate choice index + reason from parsed model payload."""
    raw_idx = data.get("option_index", None)
    idx = _normalize_option_index(raw_idx, n_legal)
    if idx is None:
        raise ValueError(f"invalid option_index {raw_idx!r} for {n_legal} legal actions")
    reason = str(data.get("reason") or "No reason provided by model.")
    return idx, reason


def choose_legal_index(
    snapshot: Dict[str, Any],
    legal_actions: List[Dict[str, Any]],
    *,
    rng: Optional[random.Random] = None,
) -> Tuple[int, Dict[str, Any]]:
    """
    Ask Ollama for an option_index into legal_actions.

    Returns (index, meta) with reason, model, repaired flag, errors.
    """
    rng = rng or random.Random()
    meta: Dict[str, Any] = {"provider": "ollama", "model": OLLAMA_MODEL, "repaired": False}

    if not legal_actions:
        raise ValueError("legal_actions empty")

    base_prompt = build_user_prompt(snapshot, legal_actions)
    n_legal = len(legal_actions)

    last_err: Optional[Exception] = None
    for attempt in range(2):
        text = _build_choice_prompt(base_prompt, attempt, n_legal - 1)
        try:
            data = _call_ollama(text)
        except Exception as ollama_err:
            last_err = ollama_err
            meta.setdefault("error", _friendly_api_error(ollama_err))
            continue

        try:
            idx, reason = _extract_choice(data, n_legal)
            meta["reason"] = reason
            if attempt == 1:
                meta["repaired"] = True
            return idx, meta
        except Exception as parse_err:
            last_err = parse_err
            meta.setdefault("error", _friendly_api_error(parse_err))

    if last_err:
        raise ValueError(
            f"Ollama did not return a valid option_index ({_friendly_api_error(last_err)})"
        ) from last_err
    raise ValueError("Ollama did not return a valid option_index")


def choose_preflop_action_with_meta(
    state: Any,
    hand_str: str,
    legal_actions: List[Dict[str, Any]],
    rng: random.Random,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Like ``choose_preflop_action`` but also returns LLM metadata (reason, model, etc.).

    `state` may be `game_engine.hu_preflop.HandState` or `full_game_engine.hu_hand.HandState`;
    bot seat is `state.actor`.
    """
    bot_seat = state.actor
    snap = hand_state_to_snapshot(state, bot_seat, hand_str)
    idx, meta = choose_legal_index(snap, legal_actions, rng=rng)
    return dict(legal_actions[idx]), meta


def choose_preflop_action(
    state: Any,
    hand_str: str,
    legal_actions: List[Dict[str, Any]],
    rng: random.Random,
) -> Dict[str, Any]:
    """
    Snapshot -> Ollama -> one legal action dict (engine shape only).

    `state` may be `game_engine.hu_preflop.HandState` or `full_game_engine.hu_hand.HandState`;
    bot seat is `state.actor`.
    """
    act, _ = choose_preflop_action_with_meta(state, hand_str, legal_actions, rng)
    return act


def choose_poker_action_with_meta(
    state: Any,
    hand_str: str,
    legal_actions: List[Dict[str, Any]],
    rng: random.Random,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Full-hand alias; identical to ``choose_preflop_action_with_meta``."""
    return choose_preflop_action_with_meta(state, hand_str, legal_actions, rng)


def choose_poker_action(
    state: Any,
    hand_str: str,
    legal_actions: List[Dict[str, Any]],
    rng: random.Random,
) -> Dict[str, Any]:
    """Alias for full-hand callers; identical to ``choose_preflop_action``."""
    return choose_preflop_action(state, hand_str, legal_actions, rng)
