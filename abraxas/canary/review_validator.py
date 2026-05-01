from __future__ import annotations

from typing import Any

from abraxas.canary.review_models import AUTHORITY_FLAGS, THRESHOLDS


def validate_review_gate_run(report: dict[str, Any]) -> None:
    if report.get("artifact") != "CANARY-REVIEW-GATE-001":
        raise ValueError("artifact mismatch")
    if report.get("schema_version") != "CanaryReviewGateRun.v1":
        raise ValueError("schema_version mismatch")
    if report.get("authority") != AUTHORITY_FLAGS:
        raise ValueError("authority mismatch")
    if report.get("thresholds") != THRESHOLDS:
        raise ValueError("threshold mismatch")
