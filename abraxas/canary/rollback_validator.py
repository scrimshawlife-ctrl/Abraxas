from __future__ import annotations

from typing import Any

from abraxas.canary.rollback_models import AUTHORITY_FLAGS


def validate_rollback_prep_run(run: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if run.get("artifact") != "CANARY-ROLLBACK-PREP-001":
        errors.append("artifact_mismatch")
    if run.get("schema_version") != "CanaryRollbackPrepRun.v1":
        errors.append("schema_version_mismatch")
    if run.get("authority") != AUTHORITY_FLAGS:
        errors.append("authority_mismatch")
    rollbacks = run.get("rollbacks") if isinstance(run.get("rollbacks"), list) else []
    counts = run.get("counts") if isinstance(run.get("counts"), dict) else {}
    if counts.get("prepared") != sum(1 for r in rollbacks if r.get("status") == "prepared"):
        errors.append("prepared_count_mismatch")
    if counts.get("not_computable") != sum(1 for r in rollbacks if r.get("status") == "not_computable"):
        errors.append("not_computable_count_mismatch")
    return errors
