from __future__ import annotations

from typing import Any

from abraxas.canary.closure_models import AUTHORITY_FLAGS


def validate_cycle_closure_report(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("artifact") != "CANARY-CYCLE-CLOSURE-REPORT-001":
        errors.append("artifact_mismatch")
    if report.get("schema_version") != "CanaryCycleClosureReport.v1":
        errors.append("schema_version_mismatch")
    if report.get("authority") != AUTHORITY_FLAGS:
        errors.append("authority_mismatch")
    if not report.get("report_id"):
        errors.append("missing_report_id")
    if not report.get("report_hash"):
        errors.append("missing_report_hash")
    return errors
