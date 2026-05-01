from __future__ import annotations

from pathlib import Path
from typing import Any

from abraxas.canary.execution_models import RUN_AUTHORITY


def validate_execution_run(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("schema_version") != "CanaryActivationExecutionRun.v1":
        errors.append("schema_version_mismatch")
    if report.get("authority") != RUN_AUTHORITY:
        errors.append("run_authority_mismatch")
    if not report.get("run_id"):
        errors.append("missing_run_id")

    executions = report.get("executions") if isinstance(report.get("executions"), list) else []
    skipped = report.get("skipped") if isinstance(report.get("skipped"), list) else []
    counts = report.get("counts") if isinstance(report.get("counts"), dict) else {}
    if counts.get("executions") != len(executions):
        errors.append("counts_executions_mismatch")
    if counts.get("skipped") != len(skipped):
        errors.append("counts_skipped_mismatch")

    ids = [e.get("execution_id") for e in executions]
    if len(ids) != len(set(ids)):
        errors.append("duplicate_execution_id")

    sandbox_root = report.get("execution_scope", {}).get("sandbox_root")
    if sandbox_root:
        root = Path(sandbox_root).resolve()
        for ex in executions:
            if ex.get("authority") != RUN_AUTHORITY:
                errors.append("execution_authority_mismatch")
            lineage = ex.get("lineage") if isinstance(ex.get("lineage"), dict) else {}
            for k in ["activation_packet_run_hash", "packet_id", "simulation_hash", "recommendation_id"]:
                if lineage.get(k) is None:
                    errors.append("missing_required_lineage")
            artifact_path = ex.get("applied_artifact", {}).get("artifact_path")
            if artifact_path:
                ap = Path(artifact_path).resolve()
                if root not in ap.parents and ap != root:
                    errors.append("artifact_path_escape")

    return errors
