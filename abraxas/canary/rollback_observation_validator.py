from __future__ import annotations

from typing import Any

from abraxas.canary.rollback_observation_models import AUTHORITY_FLAGS


def validate_rollback_observation_ledger(run: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if run.get("artifact") != "CANARY-ROLLBACK-OBSERVATION-LEDGER-001":
        errors.append("artifact_mismatch")
    if run.get("schema_version") != "CanaryRollbackObservationLedgerRun.v1":
        errors.append("schema_version_mismatch")
    if run.get("authority") != AUTHORITY_FLAGS:
        errors.append("authority_mismatch")
    obs = run.get("observations") if isinstance(run.get("observations"), list) else []
    counts = run.get("counts") if isinstance(run.get("counts"), dict) else {}
    if counts.get("observations_total") != len(obs):
        errors.append("observations_total_mismatch")
    return errors
