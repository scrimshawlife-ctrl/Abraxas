from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib
import json


REQUIRED = {
    "batch_cycle": (Path("out/registry/self_build_batch_cycle.latest.json"), "SelfBuildBatchCycle.v1"),
    "batch_trends": (Path("out/registry/self_build_batch_trends.latest.json"), "SelfBuildBatchTrends.v1"),
    "score_feedback": (Path("out/registry/self_build_score_feedback.latest.json"), "SelfBuildScoreFeedback.v1"),
    "operator_queue": (Path("out/registry/self_build_operator_queue.latest.json"), "SelfBuildOperatorQueue.v1"),
    "safety_report": (Path("out/registry/self_build_safety_report.latest.json"), "SelfBuildSafetyReport.v1"),
}


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _fail(reason: str) -> dict[str, Any]:
    payload = {
        "schema_version": "SelfBuildOperatorActionRecommendations.v1",
        "status": "NOT_COMPUTABLE",
        "reason": reason,
        "actions": [],
        "authority": {"mutation": False, "promotion": False, "execution": False, "analysis_only": True},
    }
    payload["canonical_hash"] = _sha256_text(_canonical(payload))
    return payload


def _load_required() -> dict[str, dict[str, Any]] | None:
    loaded: dict[str, dict[str, Any]] = {}
    for key, (path, schema) in REQUIRED.items():
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("schema_version") != schema:
            return None
        loaded[key] = data
    return loaded


def run_self_build_operator_action_recommender() -> dict[str, Any]:
    required = _load_required()
    if required is None:
        return _fail("MISSING_OR_INVALID_REQUIRED_ARTIFACT")

    batch_cycle = required["batch_cycle"]
    batch_trends = required["batch_trends"]
    feedback = required["score_feedback"]
    queue = required["operator_queue"]
    safety = required["safety_report"]

    actions: list[dict[str, Any]] = []
    queue_items = queue.get("items", []) if isinstance(queue.get("items"), list) else []
    flagged_targets = {
        row.get("target_path")
        for row in feedback.get("flagged_targets", [])
        if isinstance(row, dict) and isinstance(row.get("target_path"), str)
    }

    for item in sorted(queue_items, key=lambda i: i.get("approval_id", "")):
        if not isinstance(item, dict):
            continue
        approval_id = item.get("approval_id")
        target_path = item.get("target_path", "")
        if not isinstance(approval_id, str):
            continue
        flagged = target_path in flagged_targets
        action_type = "HOLD_APPROVAL_FOR_REVIEW" if flagged else "REQUEST_APPROVAL"
        confidence = 0.55 if flagged else 0.75
        reason = "Target flagged by score feedback" if flagged else "Queue item is pending operator approval"
        actions.append(
            {
                "action_id": "action-" + _sha256_text(f"{action_type}:{approval_id}:{target_path}")[:16],
                "action_type": action_type,
                "target_path": target_path,
                "approval_id": approval_id,
                "reason": reason,
                "confidence": confidence,
                "requires_operator": True,
            }
        )

    if batch_cycle.get("status") == "WAITING_FOR_APPROVAL":
        actions.append(
            {
                "action_id": "action-" + _sha256_text("WAITING_FOR_APPROVAL:REVIEW")[:16],
                "action_type": "REVIEW_PENDING_APPROVALS",
                "target_path": "",
                "approval_id": None,
                "reason": "Batch cycle is waiting for approvals",
                "confidence": 0.9,
                "requires_operator": True,
            }
        )

    if not bool(safety.get("all_plans_safe", False)):
        actions.append(
            {
                "action_id": "action-" + _sha256_text("SAFETY_GATE_BLOCKED")[:16],
                "action_type": "BLOCK_APPLY_UNTIL_SAFE",
                "target_path": "",
                "approval_id": None,
                "reason": "Safety report indicates one or more unsafe plans",
                "confidence": 0.95,
                "requires_operator": True,
            }
        )

    if "HIGH_APPROVAL_WAIT_RATIO" in batch_trends.get("flagged_trends", []):
        actions.append(
            {
                "action_id": "action-" + _sha256_text("ESCALATE_APPROVAL_WAIT")[:16],
                "action_type": "ESCALATE_APPROVAL_WAIT",
                "target_path": "",
                "approval_id": None,
                "reason": "Trend analyzer reports high approval wait ratio",
                "confidence": 0.85,
                "requires_operator": True,
            }
        )

    payload = {
        "schema_version": "SelfBuildOperatorActionRecommendations.v1",
        "status": "OK",
        "action_count": len(actions),
        "actions": sorted(actions, key=lambda a: a["action_id"]),
        "authority": {"mutation": False, "promotion": False, "execution": False, "analysis_only": True},
    }
    payload["canonical_hash"] = _sha256_text(_canonical(payload))
    return payload
