# Stabilization window tracker (v0.1)

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

DEFAULT_STATE_PATH = Path(__file__).resolve().parents[1] / "data" / "stabilization_state.json"


def load_state(path: str | None = None) -> Dict[str, Any]:
    state_path = Path(path) if path else DEFAULT_STATE_PATH
    if not state_path.exists():
        return {"advisory_cycles": {}}
    return json.loads(state_path.read_text(encoding="utf-8"))


def save_state(state: Dict[str, Any], path: str | None = None) -> None:
    state_path = Path(path) if path else DEFAULT_STATE_PATH
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(state, indent=2, sort_keys=True), encoding="utf-8"
    )


def bump_advisory_cycle(rune_id: str, state: Dict[str, Any]) -> Dict[str, Any]:
    cycles = state.setdefault("advisory_cycles", {})
    cycles[rune_id] = int(cycles.get(rune_id, 0)) + 1
    return state


def advisory_cycles(state: Dict[str, Any], rune_id: str) -> int:
    return int(state.get("advisory_cycles", {}).get(rune_id, 0))
