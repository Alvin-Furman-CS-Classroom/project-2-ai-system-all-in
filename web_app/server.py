"""
Flask web UI: human (seat 0) vs bot (seat 1), pre-flop + showdown runout.

The bot opponent is chosen per session via the UI: random legal actions, Module 1+2
(rule-based + A* bet sizing), or Module 3 Monte Carlo rollouts (not MCTS).

Human actions return immediately. The bot moves only when the client POSTs
/api/advance_bot (after a client-side "thinking" delay).
"""

from __future__ import annotations

import os
import secrets
import sys
import random
import threading
from pathlib import Path
from typing import Any, Dict, Optional

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from flask import Flask, jsonify, render_template, request

from game_engine.bot_agents import DEFAULT_BOT_AGENT, normalize_agent, pick_bot_action
from game_engine.hu_preflop import (
    HandState,
    apply_action,
    legal_actions,
    new_hand,
    raise_amount_range,
)

app = Flask(
    __name__,
    template_folder=str(Path(__file__).parent / "templates"),
    static_folder=str(Path(__file__).parent / "static"),
)
app.secret_key = os.environ.get("FLASK_SECRET", "dev-preflop-showdown-key")

SESSIONS: Dict[str, Dict[str, Any]] = {}
SESSION_BOT_LOCKS: Dict[str, threading.Lock] = {}
STARTING_STACK = 2000
BB = 20


def _bot_lock(sid: str) -> threading.Lock:
    if sid not in SESSION_BOT_LOCKS:
        SESSION_BOT_LOCKS[sid] = threading.Lock()
    return SESSION_BOT_LOCKS[sid]


def _session_id() -> str:
    sid = request.cookies.get("sid")
    if sid and sid in SESSIONS:
        return sid
    return secrets.token_hex(16)


def _ensure_session() -> str:
    sid = _session_id()
    if sid not in SESSIONS:
        SESSIONS[sid] = {
            "stacks": [STARTING_STACK, STARTING_STACK],
            "button": 0,
            "rng": random.Random(),
            "bot_agent": DEFAULT_BOT_AGENT,
        }
    return sid


def _bot_agent_for_session(sid: str) -> str:
    s = SESSIONS.get(sid)
    if not s:
        return DEFAULT_BOT_AGENT
    if "bot_agent" not in s:
        s["bot_agent"] = DEFAULT_BOT_AGENT
    return normalize_agent(s.get("bot_agent"))


def state_to_json(state: HandState, human_seat: int = 0) -> Dict[str, Any]:
    """Serialize hand; hide opponent hole cards until hand is over."""
    show_all = state.phase == "hand_over"
    h0 = [str(c) for c in state.hole_cards[0]]
    h1 = [str(c) for c in state.hole_cards[1]]
    if not show_all:
        if human_seat == 0:
            h1 = ["??", "??"]
        else:
            h0 = ["??", "??"]

    out: Dict[str, Any] = {
        "phase": state.phase,
        "actor": state.actor,
        "pot": state.pot,
        "stacks": list(state.stacks),
        "round_contrib": list(state.round_contrib),
        "to_call": [state.to_call(0), state.to_call(1)],
        "hole_cards": [h0, h1],
        "board": [str(c) for c in state.board],
        "winner": state.winner,
        "button": state.button,
        "bb_chips": state.bb_chips,
        "history_tail": state.history[-6:],
    }
    if state.phase == "preflop" and state.actor == human_seat:
        out["legal_actions"] = legal_actions(state)
        rr = raise_amount_range(state)
        if rr:
            out["raise_range"] = rr
    return out


def run_bot_until_human(state: HandState, rng: random.Random, sid: Optional[str] = None) -> None:
    """Run bot action(s) until it's human's turn or hand is over. No artificial delay."""
    lock = _bot_lock(sid) if sid else None

    def _run() -> None:
        ag = _bot_agent_for_session(sid) if sid else DEFAULT_BOT_AGENT
        while state.phase == "preflop" and state.actor == 1:
            act = pick_bot_action(ag, state, rng)
            apply_action(state, act)

    if lock:
        with lock:
            _run()
    else:
        _run()


@app.route("/")
def index():
    sid = _ensure_session()
    resp = app.make_response(render_template("index.html", starting_stack=STARTING_STACK))
    resp.set_cookie("sid", sid, httponly=True, samesite="Lax")
    return resp


@app.route("/api/state", methods=["GET"])
def api_state():
    """Current state only — does not advance the bot."""
    sid = _ensure_session()
    s = SESSIONS.get(sid)
    if not s or "hand" not in s:
        return jsonify(
            {
                "needs_new_hand": True,
                "stacks": s.get("stacks", [STARTING_STACK, STARTING_STACK]) if s else [STARTING_STACK, STARTING_STACK],
                "bot_agent": _bot_agent_for_session(sid),
            }
        )
    state: HandState = s["hand"]
    resp = jsonify({"state": state_to_json(state, human_seat=0), "bot_agent": _bot_agent_for_session(sid)})
    resp.set_cookie("sid", sid, httponly=True, samesite="Lax")
    return resp


@app.route("/api/new_hand", methods=["POST"])
def api_new_hand():
    sid = _ensure_session()
    s = SESSIONS[sid]
    data = request.get_json(silent=True) or {}
    stacks = data.get("stacks")
    if stacks and len(stacks) == 2:
        s["stacks"] = [int(stacks[0]), int(stacks[1])]
    btn = s.get("button", 0)
    state = new_hand(s["stacks"], rng=s["rng"], button=btn)
    s["hand"] = state
    s["button"] = 1 - btn
    resp = jsonify({"state": state_to_json(state, human_seat=0), "bot_agent": _bot_agent_for_session(sid)})
    resp.set_cookie("sid", sid, httponly=True, samesite="Lax")
    return resp


@app.route("/api/set_agent", methods=["POST"])
def api_set_agent():
    """Set opponent agent for this session: random | m12 | m3."""
    sid = _ensure_session()
    body = request.get_json(silent=True) or {}
    raw = body.get("agent", DEFAULT_BOT_AGENT)
    ag = normalize_agent(str(raw) if raw is not None else DEFAULT_BOT_AGENT)
    SESSIONS[sid]["bot_agent"] = ag
    resp = jsonify({"ok": True, "bot_agent": ag})
    resp.set_cookie("sid", sid, httponly=True, samesite="Lax")
    return resp


def _match_legal(body: Dict[str, Any], legal: list, state: HandState) -> Optional[Dict[str, Any]]:
    kind = body.get("kind")
    if kind == "raise_to":
        try:
            total = int(body.get("total"))
        except (TypeError, ValueError):
            return None
        rr = raise_amount_range(state)
        if rr and rr["min"] <= total <= rr["max"]:
            return {"kind": "raise_to", "total": total}
        return None
    for a in legal:
        if a["kind"] != kind:
            continue
        return a
    return None


@app.route("/api/action", methods=["POST"])
def api_action():
    """Apply human action only; returns immediately (bot moves later via /api/advance_bot)."""
    sid = _ensure_session()
    if sid not in SESSIONS or "hand" not in SESSIONS[sid]:
        return jsonify({"error": "No hand"}), 400
    s = SESSIONS[sid]
    state: HandState = s["hand"]
    if state.phase != "preflop" or state.actor != 0:
        return jsonify({"error": "Not your turn or hand over"}), 400
    body = request.get_json(force=True, silent=True) or {}
    legal = legal_actions(state)
    matched = _match_legal(body, legal, state)
    if not matched:
        return jsonify({"error": "Illegal action", "legal": legal}), 400
    action: Dict[str, Any] = dict(matched)
    apply_action(state, action)
    if state.phase == "hand_over":
        s["stacks"] = list(state.stacks)
    resp = jsonify({"state": state_to_json(state, human_seat=0), "bot_agent": _bot_agent_for_session(sid)})
    resp.set_cookie("sid", sid, httponly=True, samesite="Lax")
    return resp


@app.route("/api/advance_bot", methods=["POST"])
def api_advance_bot():
    """Run the bot after the client has waited (thinking delay). Idempotent if not bot's turn."""
    sid = _ensure_session()
    if sid not in SESSIONS or "hand" not in SESSIONS[sid]:
        return jsonify({"error": "No hand"}), 400
    s = SESSIONS[sid]
    state: HandState = s["hand"]
    if state.phase == "preflop" and state.actor == 1:
        run_bot_until_human(state, s["rng"], sid=sid)
    if state.phase == "hand_over":
        s["stacks"] = list(state.stacks)
    resp = jsonify({"state": state_to_json(state, human_seat=0), "bot_agent": _bot_agent_for_session(sid)})
    resp.set_cookie("sid", sid, httponly=True, samesite="Lax")
    return resp


@app.route("/api/legal", methods=["GET"])
def api_legal():
    sid = _ensure_session()
    s = SESSIONS.get(sid)
    if not s or "hand" not in s:
        return jsonify({"actions": []}), 200
    state: HandState = s["hand"]
    return jsonify({"actions": legal_actions(state) if state.phase == "preflop" else []})


def main():
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)), debug=True)


if __name__ == "__main__":
    main()
