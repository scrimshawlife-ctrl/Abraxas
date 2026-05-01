from __future__ import annotations

from typing import Any

from abraxas.canary.rollback_review_models import AUTHORITY_FLAGS


def validate_rollback_review_gate_run(run: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if run.get("artifact") != "CANARY-ROLLBACK-REVIEW-GATE-001":
        errors.append("artifact_mismatch")
    if run.get("schema_version") != "CanaryRollbackReviewGateRun.v1":
        errors.append("schema_version_mismatch")
    if run.get("authority") != AUTHORITY_FLAGS:
        errors.append("authority_mismatch")
    recs = run.get("recommendations") if isinstance(run.get("recommendations"), list) else []
    counts = run.get("counts") if isinstance(run.get("counts"), dict) else {}
    for key in ["recommend_approve_for_rollback_review", "recommend_hold", "recommend_reject", "not_computable"]:
        if counts.get(key) != sum(1 for r in recs if r.get("status") == key):
            errors.append(f"count_mismatch:{key}")
    return errors
