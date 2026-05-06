#!/usr/bin/env python3
"""Run adaptive sandbox - v2.0.5 governed adaptive sandbox engine.

Behavior:
- loads latest governed state
- generates sandbox branch
- applies deterministic candidate mutations
- emits sandbox artifacts

Writes:
  out/sandbox/latest.json
  out/promotion_candidates/latest.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.models.governance import Authority
from core.sandbox.runtime import run_adaptive_sandbox

AUTHORITY = Authority(
    authority_id="auth.sandbox.001",
    actor="system.sandbox",
    locked=True,
    scope="sandbox_only",
)

# Deterministic candidate transitions for sandbox
CANDIDATE_TRANSITIONS = [
    {
        "mutation_type": "route_adjustment",
        "transition_hashes": ["hash_route_001", "hash_route_002"],
    },
    {
        "mutation_type": "validation_adjustment",
        "transition_hashes": ["hash_validate_001"],
    },
]


def load_governed_state() -> dict:
    """Load the latest governed state from state engine output."""
    state_path = Path("out/state_engine/latest.json")
    if state_path.exists():
        data = json.loads(state_path.read_text(encoding="utf-8"))
        return {
            "state_hash": data.get("state_hash", "a" * 64),
            "generation": data.get("transition_count", 0),
            "stabilization_state": data.get("stabilization_state", "stable"),
        }
    # Bootstrap default
    return {
        "state_hash": "bootstrap_state_" + "0" * 48,
        "generation": 0,
        "stabilization_state": "stable",
    }


def main() -> None:
    # Ensure state engine has run
    state_engine_path = Path("out/state_engine/latest.json")
    if not state_engine_path.exists():
        print("State engine output not found. Running state engine first...")
        from scripts.run_state_engine import main as run_se
        run_se()

    governed_state = load_governed_state()

    print(f"Loaded governed state: generation={governed_state['generation']}, "
          f"stabilization={governed_state['stabilization_state']}")

    result = run_adaptive_sandbox(
        governed_state=governed_state,
        transition_packets=CANDIDATE_TRANSITIONS,
        replay_packets_input=[],  # Self-replay (always matches)
        authority=AUTHORITY,
        out_dir=Path("out/sandbox"),
    )

    branch = result["branch"]
    stab = result["stabilization"]
    promo = result["promotion_candidate"]
    sim_run = result["simulation_run"]

    print(f"Adaptive sandbox complete:")
    print(f"  Branch ID: {branch.branch_id}")
    print(f"  Branch hash: {branch.deterministic_branch_hash[:16]}...")
    print(f"  Mutation count: {len(result['mutation_packets'])}")
    print(f"  Replay results: {len(result['replay_results'])}")
    print(f"  Stabilization: {stab.stabilization_state}")
    print(f"  Promotion allowed: {promo.promotion_allowed}")
    print(f"  Run status: {sim_run.status}")
    print(f"  out/sandbox/latest.json")
    print(f"  out/promotion_candidates/latest.json")


if __name__ == "__main__":
    main()
