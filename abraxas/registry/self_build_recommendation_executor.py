from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib
import json
import os

from .self_build_approval_setter import run_self_build_approval_setter
from .self_build_batch_cycle import run_self_build_batch_cycle
from .self_build_recommendation_execution_ledger import append_execution_entry

RECOMMENDER_PATH = Path("out/registry/self_build_operator_action_recommendations.latest.json")


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _authority() -> dict[str, Any]:
    return {
        "mutation": False,
        "promotion": False,
        "execution": False,
        "operator_intent_write": True,
        "artifact_mutation": False,
        "recommendation_execution_only": True,
    }


def _result(status: str, action_id: str | None, action_type: str | None, **extra: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": "SelfBuildRecommendationExecution.v1",
        "status": status,
        "action_id": action_id,
        "action_type": action_type,
        "authority": _authority(),
    }
    payload.update(extra)
    payload["canonical_hash"] = _sha256_text(_canonical(payload))
    return payload


def _finalize(payload: dict[str, Any]) -> dict[str, Any]:
    append_execution_entry(payload)
    return payload


def _load_recommendations() -> dict[str, Any] | None:
    if not RECOMMENDER_PATH.exists():
        return None
    loaded = json.loads(RECOMMENDER_PATH.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict) or loaded.get("schema_version") != "SelfBuildOperatorActionRecommendations.v1":
        return None
    return loaded


def run_self_build_recommendation_executor(action_id: str | None = None) -> dict[str, Any]:
    rec = _load_recommendations()
    if rec is None:
        return _finalize(_result("NOT_COMPUTABLE", action_id, None, reason="MISSING_OR_INVALID_RECOMMENDATIONS"))

    selected_action_id = action_id or os.environ.get("ACTION_ID")
    if not selected_action_id:
        return _finalize(_result("NOT_COMPUTABLE", None, None, reason="MISSING_ACTION_ID"))

    actions = rec.get("actions", []) if isinstance(rec.get("actions"), list) else []
    action = next((a for a in actions if isinstance(a, dict) and a.get("action_id") == selected_action_id), None)
    if action is None:
        return _finalize(_result("NOT_COMPUTABLE", selected_action_id, None, reason="UNKNOWN_ACTION_ID"))

    action_type = action.get("action_type")
    approval_id = action.get("approval_id")

    if action_type in {"REQUEST_APPROVAL", "APPROVE_ONE"}:
        if not isinstance(approval_id, str):
            return _finalize(_result("NOT_COMPUTABLE", selected_action_id, str(action_type), reason="MISSING_APPROVAL_ID"))
        write_result = run_self_build_approval_setter([approval_id], [])
        return _finalize(_result("EXECUTED", selected_action_id, "APPROVE_ONE", approval_write=write_result, batch_cycle_hash=None))

    if action_type in {"HOLD_APPROVAL_FOR_REVIEW", "HOLD"}:
        return _finalize(
            _result(
                "EXECUTED",
                selected_action_id,
                "HOLD",
                approval_write={"status": "NO_OP", "detail": "Operator hold action; no approval write performed"},
                batch_cycle_hash=None,
            )
        )

    if action_type in {"RUN_BATCH", "REVIEW_PENDING_APPROVALS", "ESCALATE_APPROVAL_WAIT"}:
        batch = run_self_build_batch_cycle()
        return _finalize(_result("EXECUTED", selected_action_id, "RUN_BATCH", approval_write=None, batch_cycle_hash=batch.get("canonical_hash")))

    if action_type == "REJECT_TARGET":
        if not isinstance(approval_id, str):
            return _finalize(_result("NOT_COMPUTABLE", selected_action_id, str(action_type), reason="MISSING_APPROVAL_ID"))
        write_result = run_self_build_approval_setter([], [approval_id])
        return _finalize(_result("EXECUTED", selected_action_id, "REJECT_TARGET", approval_write=write_result, batch_cycle_hash=None))

    return _finalize(_result("NOT_COMPUTABLE", selected_action_id, str(action_type), reason="UNSUPPORTED_ACTION_TYPE"))
