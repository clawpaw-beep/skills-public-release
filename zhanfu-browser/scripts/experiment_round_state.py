#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def load_state(path: Path, max_rounds: int) -> dict[str, Any]:
    if path.exists():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                payload.setdefault("rounds_completed", 0)
                payload.setdefault("max_rounds", max_rounds)
                payload.setdefault("history", [])
                return payload
        except Exception:
            pass
    return {
        "rounds_completed": 0,
        "max_rounds": max_rounds,
        "history": [],
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def claim_next_round(path: Path, max_rounds: int) -> tuple[dict[str, Any], int | None]:
    state = load_state(path, max_rounds)
    state["max_rounds"] = max_rounds
    completed = int(state.get("rounds_completed", 0) or 0)
    if completed >= max_rounds:
        state["blocked_at"] = datetime.now().isoformat(timespec="seconds")
        save_state(path, state)
        return state, None
    next_round = completed + 1
    state["rounds_completed"] = next_round
    state["last_round_started_at"] = datetime.now().isoformat(timespec="seconds")
    state["last_round"] = next_round
    save_state(path, state)
    return state, next_round


def record_round_result(path: Path, round_number: int, status: str, run_dir: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    existing = load_state(path, 10)
    state = load_state(path, max_rounds=int(existing.get("max_rounds", 10)))
    history = state.setdefault("history", [])
    entry = {
        "round": round_number,
        "status": status,
        "run_dir": run_dir,
        "finished_at": datetime.now().isoformat(timespec="seconds"),
    }
    if extra:
        entry.update(extra)
    history.append(entry)
    state["history"] = history[-30:]
    state["last_status"] = status
    state["last_run_dir"] = run_dir
    state["last_round_finished_at"] = entry["finished_at"]
    save_state(path, state)
    return state
