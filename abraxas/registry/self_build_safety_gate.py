from __future__ import annotations

from typing import Any
import hashlib
import json

from .green_state_attestation import run_green_state_attestation
from .self_build_patch_plan import run_self_build_patch_plan


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _is_safe_plan(plan: dict[str, Any]) -> list[str]:
    violations: list[str] = []

    target_path = plan.get("target_path", "")
    if not isinstance(target_path, str) or not target_path.startswith("out/"):
        violations.append("invalid_target_scope")

    raw_text = json.dumps(plan, sort_keys=True).lower()
    if "delete" in raw_text:
        violations.append("forbidden_term:delete")
    if "enable_mutation" in raw_text and "must_not_enable_mutation" not in raw_text:
        violations.append("forbidden_term:mutation")
    if "enable_promotion" in raw_text and "must_not_enable_promotion" not in raw_text:
        violations.append("forbidden_term:promotion")

    return violations


def run_self_build_safety_gate() -> dict[str, Any]:
    patch_plan = run_self_build_patch_plan()
    green = run_green_state_attestation()

    results = []
    for plan in patch_plan["plans"]:
        violations = _is_safe_plan(plan)
        results.append(
            {
                "target_path": plan["target_path"],
                "safe": len(violations) == 0,
                "violations": violations,
            }
        )

    all_safe = all(item["safe"] for item in results)
    payload = {
        "schema_version": "SelfBuildSafetyReport.v1",
        "green_state_verified": green["operator_health"] == "GREEN",
        "all_plans_safe": all_safe,
        "results": results,
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
