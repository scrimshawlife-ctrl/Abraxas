from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Mapping

from abx.repair.scenario_engine import run_scenario_batch


def _priority_and_action(result: Mapping[str, Any], top_scenario_id: str) -> tuple[str, str]:
    status = str(result.get("scenario_status", "NOT_COMPUTABLE"))
    safety = result.get("safety_flags", {}) if isinstance(result.get("safety_flags", {}), dict) else {}
    unsafe = any(bool(safety.get(k, False)) for k in ["execution_triggered", "runtime_mutation", "authority_leak_detected"])
    if unsafe:
        return "P1", "REJECT"
    if status == "PASS" and str(result.get("scenario_id", "")) == top_scenario_id:
        return "P1", "APPROVE_FOR_SANDBOX_DESIGN"
    if status == "PASS":
        return "P2", "DEFER"
    return "P1", "REJECT"


def build_scenario_review_queue(batch: Mapping[str, Any] | None = None) -> Dict[str, Any]:
    if batch is None:
        batch = run_scenario_batch()
    results = list(batch.get("results", [])) if isinstance(batch.get("results", []), list) else []
    top = str(batch.get("top_scenario_id", "NOT_COMPUTABLE"))

    items = []
    for idx, result in enumerate(results, start=1):
        priority, action = _priority_and_action(result, top)
        items.append(
            {
                "schema_version": "OperatorScenarioReviewItem.v1",
                "review_id": f"review.{result.get('scenario_id', idx)}",
                "scenario_id": str(result.get("scenario_id", "NOT_COMPUTABLE")),
                "scenario_type": str(result.get("scenario_type", "NOT_COMPUTABLE")),
                "priority": priority,
                "decision_type": "REVIEW_SCENARIO",
                "rank": idx,
                "score": float(result.get("score", 0.0) or 0.0),
                "risk_level": str(result.get("risk_level", "MEDIUM")),
                "rank_reason": str(result.get("rank_reason", "deterministic")),
                "recommended_action": action,
                "operator_required": True,
                "auto_apply_allowed": False,
                "execution_allowed": False,
                "runtime_mutation_allowed": False,
                "evidence_refs": [str(batch.get("batch_id", "NOT_COMPUTABLE")), str(result.get("binding_id", "NOT_COMPUTABLE"))],
            }
        )

    priority_rank = {"P1": 0, "P2": 1}
    items.sort(key=lambda i: (priority_rank.get(str(i["priority"]), 9), int(i["rank"]), -float(i["score"]), str(i["scenario_id"])))

    p1_count = sum(1 for i in items if i["priority"] == "P1")
    p2_count = sum(1 for i in items if i["priority"] == "P2")
    return {
        "schema_version": "OperatorScenarioReviewQueue.v1",
        "queue_id": f"scenario-queue-{str(batch.get('batch_id', 'NOT_COMPUTABLE'))}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_batch_id": str(batch.get("batch_id", "NOT_COMPUTABLE")),
        "item_count": len(items),
        "p1_count": p1_count,
        "p2_count": p2_count,
        "top_review_id": str(items[0]["review_id"]) if items else "NOT_COMPUTABLE",
        "items": items,
        "execution_allowed": False,
        "runtime_mutation_allowed": False,
        "auto_apply_allowed": False,
    }


def record_scenario_review_decision(queue: Mapping[str, Any], review_id: str, decision: str) -> Dict[str, Any]:
    _ = queue
    return {
        "schema_version": "ScenarioReviewReceipt.v1",
        "operator_decision": decision,
        "decision_scope": "SANDBOX_DESIGN_ONLY",
        "execution_allowed": False,
        "runtime_mutation_allowed": False,
        "files_modified": [],
        "status": "RECORDED",
        "review_id": review_id,
    }
