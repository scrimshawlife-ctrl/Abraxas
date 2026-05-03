from __future__ import annotations

from typing import Any
import hashlib
import json

from .self_build_proposal import run_self_build_proposal


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def run_self_build_patch_plan() -> dict[str, Any]:
    proposal = run_self_build_proposal()
    plans = []
    for item in proposal["proposals"]:
        target = item["target_path"]
        plans.append(
            {
                "target_path": target,
                "patch_type": "ADD_MINIMAL_COMPUTE",
                "implementation_strategy": [
                    "replace NOT_COMPUTABLE with deterministic placeholder logic",
                    "preserve schema_version",
                    "preserve authority flags",
                ],
                "test_requirements": [
                    f"assert file exists: {target}",
                    f"assert status != NOT_COMPUTABLE after patch",
                ],
                "validation_commands": [
                    "python scripts/run_binding_validator.py",
                    "python scripts/run_operator_closure_card.py",
                    "python scripts/run_invariance_harness.py",
                ],
                "rollback": "revert to NOT_COMPUTABLE stub if validation fails",
            }
        )

    payload = {
        "schema_version": "SelfBuildPatchPlan.v1",
        "plan_count": len(plans),
        "plans": plans,
    }
    payload_hash = _sha256_text(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return {
        **payload,
        "canonical_hash": payload_hash,
        "authority": {
            "mutation": False,
            "promotion": False,
            "execution": False,
            "observe_only": True,
        },
    }
