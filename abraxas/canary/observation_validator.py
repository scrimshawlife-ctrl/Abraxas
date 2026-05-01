from __future__ import annotations

from typing import Any

from abraxas.canary.observation_models import AUTHORITY_FLAGS


def validate_observation_ledger_run(run: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if run.get("artifact") != "CANARY-OBSERVATION-LEDGER-001":
        errors.append("artifact_mismatch")
    if run.get("schema_version") != "CanaryObservationLedgerRun.v1":
        errors.append("schema_version_mismatch")
    if run.get("authority") != AUTHORITY_FLAGS:
        errors.append("authority_mismatch")
    entries = run.get("entries") if isinstance(run.get("entries"), list) else []
    counts = run.get("counts") if isinstance(run.get("counts"), dict) else {}
    if counts.get("entries_total") != len(entries):
        errors.append("entries_total_mismatch")
    return errors
