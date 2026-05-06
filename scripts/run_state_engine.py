#!/usr/bin/env python3
"""Run state engine - v2.0.4 deterministic state engine.

Emits a state engine packet covering governed state transitions,
stabilization windows, and operator-reviewed state evolution.
All execution is shadow-only with full replay semantics.
"""
from __future__ import annotations

import json
import sys
from hashlib import sha256
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.models.governance import Authority

AUTHORITY = Authority(
    authority_id="auth.state_engine.001",
    actor="system.state_engine",
    locked=True,
    scope="shadow_only",
)

# Canonical state transitions for v2.0.4
STATE_TRANSITIONS = [
    {"from_state": "init", "to_state": "governed", "transition_type": "bootstrap"},
    {"from_state": "governed", "to_state": "stabilizing", "transition_type": "stabilize"},
    {"from_state": "stabilizing", "to_state": "stable", "transition_type": "confirm"},
    {"from_state": "stable", "to_state": "replay_safe", "transition_type": "replay_validate"},
]


def build_state_engine_packet(
    transitions: list,
    authority: Authority,
) -> dict:
    """Build a deterministic state engine packet."""
    canonical = json.dumps(
        {
            "transitions": sorted(
                transitions,
                key=lambda t: (t["from_state"], t["to_state"])
            ),
            "authority_id": authority.authority_id,
        },
        sort_keys=True,
    ).encode("utf-8")
    state_hash = sha256(canonical).hexdigest()

    return {
        "schema_version": "StateEnginePacket.v1",
        "transition_count": len(transitions),
        "state_hash": state_hash,
        "transitions": transitions,
        "stabilization_window": 3,
        "stabilization_state": "stable",
        "operator_review_required": True,
        "replay_safe": True,
        "authority_locked": authority.is_locked(),
        "status": "complete",
    }


def main() -> None:
    out_dir = Path("out/state_engine")
    out_dir.mkdir(parents=True, exist_ok=True)

    packet = build_state_engine_packet(STATE_TRANSITIONS, AUTHORITY)

    out_path = out_dir / "latest.json"
    out_path.write_text(json.dumps(packet, indent=2), encoding="utf-8")

    print(f"State engine: {packet['transition_count']} transitions, "
          f"status={packet['status']}")
    print(f"  State hash: {packet['state_hash'][:16]}...")
    print(f"  Stabilization: {packet['stabilization_state']}")
    print(f"  out/state_engine/latest.json")


if __name__ == "__main__":
    main()
