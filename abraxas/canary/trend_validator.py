from __future__ import annotations

from typing import Any

from abraxas.canary.trend_models import AUTHORITY_FLAGS


def validate_cycle_trend_analysis(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("artifact") != "CANARY-CYCLE-TREND-ANALYSIS-001":
        errors.append("artifact_mismatch")
    if report.get("schema_version") != "CanaryCycleTrendAnalysis.v1":
        errors.append("schema_version_mismatch")
    if report.get("authority") != AUTHORITY_FLAGS:
        errors.append("authority_mismatch")
    if not report.get("analysis_id"):
        errors.append("missing_analysis_id")
    if not report.get("analysis_hash"):
        errors.append("missing_analysis_hash")
    return errors
