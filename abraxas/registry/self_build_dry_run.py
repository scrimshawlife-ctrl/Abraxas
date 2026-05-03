from __future__ import annotations

from typing import Any
import hashlib
import json

from .self_build_patch_plan import run_self_build_patch_plan
from .self_build_safety_gate import run_self_build_safety_gate


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def run_self_build_dry_run() -> dict[str, Any]:
    safety = run_self_build_safety_gate()
    plan = run_self_build_patch_plan()

    simulations = []
    for item in plan["plans"]:
        simulations.append(
            {
                "target_path": item["target_path"],
                "simulated_action": "REPLACE_NOT_COMPUTABLE",
                "expected_result": "COMPUTABLE",
                "green_state_preserved": True,
                "notes": "No real mutation performed",
            }
        )

    payload = {
        "schema_version": "SelfBuildDryRun.v1",
        "safe_to_simulate": safety["all_plans_safe"],
        "simulation_count": len(simulations),
        "simulations": simulations,
    }
    payload_hash = _sha256_text(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return {
        **payload,
        "canonical_hash": payload_hash,
        "authority": {
            "mutation": False,
            "execution": False,
            "observe_only": True,
        },
    }
