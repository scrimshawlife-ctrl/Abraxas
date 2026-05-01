from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from typing import Any, Mapping

from abraxas.canary.rollback_review_models import AUTHORITY_FLAGS
from abraxas.core.canonical import canonical_json


def _sha(obj: Any) -> str:
    return sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def build_rollback_review_gate(rollback_prep_run: Mapping[str, Any]) -> dict:
    data = deepcopy(dict(rollback_prep_run))
    rollbacks = data.get("rollbacks") if isinstance(data.get("rollbacks"), list) else []

    recommendations: list[dict] = []
    counts = {
        "rollback_preps_total": len(rollbacks),
        "recommend_approve_for_rollback_review": 0,
        "recommend_hold": 0,
        "recommend_reject": 0,
        "not_computable": 0,
    }

    ordered = sorted((r for r in rollbacks if isinstance(r, dict)), key=lambda r: (str(r.get("source_key", "")), str(r.get("rollback_id", ""))))

    for rb in ordered:
        safety = rb.get("safety") if isinstance(rb.get("safety"), dict) else {}
        plan = rb.get("rollback_plan") if isinstance(rb.get("rollback_plan"), dict) else {}
        lineage = rb.get("lineage") if isinstance(rb.get("lineage"), dict) else {}

        rb_status = rb.get("status")
        if rb_status == "not_computable":
            status = "not_computable"
            reason = f"rollback_prep_not_computable:{safety.get('reason')}"
        elif rb_status != "prepared":
            status = "not_computable"
            reason = f"unexpected_rollback_status:{rb_status}"
        elif safety.get("replayable") is not True:
            status = "recommend_hold"
            reason = "not_replayable"
        elif safety.get("rollback_prepared") is not True:
            status = "recommend_hold"
            reason = "rollback_not_prepared"
        elif rb.get("rollback_key") is None:
            status = "not_computable"
            reason = "missing_rollback_key"
        else:
            status = "recommend_approve_for_rollback_review"
            reason = "rollback_ready_for_review"

        basis = {
            "rollback_status": rb_status,
            "replayable": bool(safety.get("replayable")),
            "rollback_prepared": bool(safety.get("rollback_prepared")),
            "artifact_hash": plan.get("artifact_hash"),
            "artifact_path": plan.get("artifact_path"),
            "reason": reason,
        }
        lineage_obj = {
            "rollback_hash": _sha(rb),
            "observation_hash": lineage.get("observation_hash"),
            "execution_hash": lineage.get("execution_hash"),
        }

        rec_base = {
            "recommendation_version": "CanaryRollbackReviewRecommendation.v1",
            "rollback_id": rb.get("rollback_id"),
            "observation_id": rb.get("observation_id"),
            "execution_id": rb.get("execution_id"),
            "source_key": str(rb.get("source_key", "")),
            "status": status,
            "basis": basis,
            "lineage": lineage_obj,
            "authority": dict(AUTHORITY_FLAGS),
        }
        recommendation_id = _sha(rec_base)

        rec = {
            **rec_base,
            "recommendation_id": recommendation_id,
        }
        recommendations.append(rec)
        counts[status] += 1

    recommendations = sorted(recommendations, key=lambda r: (r["source_key"], r["recommendation_id"]))

    return {
        "artifact": "CANARY-ROLLBACK-REVIEW-GATE-001",
        "schema_version": "CanaryRollbackReviewGateRun.v1",
        "authority": dict(AUTHORITY_FLAGS),
        "counts": counts,
        "recommendations": recommendations,
    }
