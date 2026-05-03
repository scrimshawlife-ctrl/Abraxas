from __future__ import annotations

from typing import Any
import hashlib
import json

from .self_build_dry_run import run_self_build_dry_run
from .self_build_patch_plan import run_self_build_patch_plan
from .self_build_safety_gate import run_self_build_safety_gate


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _approval_id(target_path: str, action: str) -> str:
    return "approval-" + _sha256_text(f"{target_path}:{action}")[:16]


def run_self_build_operator_queue() -> dict[str, Any]:
    dry_run = run_self_build_dry_run()
    safety = run_self_build_safety_gate()
    patch_plan = run_self_build_patch_plan()

    plan_by_target = {plan["target_path"]: plan for plan in patch_plan["plans"]}

    items = []
    for sim in dry_run["simulations"]:
        target = sim["target_path"]
        action = sim["simulated_action"]
        plan = plan_by_target.get(target, {})
        items.append(
            {
                "approval_id": _approval_id(target, action),
                "target_path": target,
                "proposed_action": action,
                "expected_result": sim["expected_result"],
                "approval_status": "PENDING_OPERATOR_APPROVAL",
                "safety_verified": safety["all_plans_safe"],
                "green_state_preserved_predicted": sim["green_state_preserved"],
                "validation_commands": plan.get("validation_commands", []),
                "rollback": plan.get("rollback", "NOT_AVAILABLE"),
            }
        )

    payload = {
        "schema_version": "SelfBuildOperatorQueue.v1",
        "queue_count": len(items),
        "items": sorted(items, key=lambda item: item["approval_id"]),
        "authority": {
            "mutation": False,
            "promotion": False,
            "execution": False,
            "operator_approval_required": True,
            "observe_only": True,
        },
    }
    payload_hash = _sha256_text(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return {
        **payload,
        "canonical_hash": payload_hash,
    }
