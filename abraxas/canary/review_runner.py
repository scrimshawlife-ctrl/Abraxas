from __future__ import annotations

from typing import Any

from abraxas.canary.review_gate import build_recommendations
from abraxas.canary.review_models import AUTHORITY_FLAGS, THRESHOLDS
from abraxas.canary.review_validator import validate_review_gate_run


def build_canary_review_gate_run(
    simulation_run: dict[str, Any],
    overlay_run: dict[str, Any],
    ledger_run: dict[str, Any],
) -> dict[str, Any]:
    recommendations = build_recommendations(simulation_run, overlay_run, ledger_run)
    counts = {
        "simulations_total": len(recommendations),
        "recommend_approve_for_activation_review": 0,
        "recommend_hold": 0,
        "recommend_reject": 0,
        "not_computable": 0,
    }
    for rec in recommendations:
        status = rec.get("status")
        if status in counts:
            counts[status] += 1

    report = {
        "artifact": "CANARY-REVIEW-GATE-001",
        "schema_version": "CanaryReviewGateRun.v1",
        "authority": dict(AUTHORITY_FLAGS),
        "thresholds": dict(THRESHOLDS),
        "counts": counts,
        "recommendations": recommendations,
    }
    validate_review_gate_run(report)
    return report
