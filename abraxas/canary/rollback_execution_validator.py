from __future__ import annotations

from typing import Any

from abraxas.canary.rollback_execution_models import AUTHORITY_FLAGS


def validate_rollback_execution_run(run: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if run.get("artifact") != "CANARY-ROLLBACK-EXECUTOR-001":
        errors.append("artifact_mismatch")
    if run.get("schema_version") != "CanaryRollbackExecutionRun.v1":
        errors.append("schema_version_mismatch")
    if run.get("authority") != AUTHORITY_FLAGS:
        errors.append("authority_mismatch")
    ex = run.get("executions") if isinstance(run.get("executions"), list) else []
    counts = run.get("counts") if isinstance(run.get("counts"), dict) else {}
    for key in ["completed", "skipped", "blocked", "failed"]:
        if counts.get(key) != sum(1 for e in ex if e.get("execution_status") == key):
            errors.append(f"count_mismatch:{key}")
    return errors
