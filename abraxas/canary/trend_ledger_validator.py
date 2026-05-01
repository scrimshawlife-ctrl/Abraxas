from __future__ import annotations

from typing import Any

from abraxas.canary.trend_ledger_models import AUTHORITY_FLAGS


def validate_trend_ledger(run: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if run.get("artifact") != "CANARY-TREND-LEDGER-001":
        errors.append("artifact_mismatch")
    if run.get("schema_version") != "CanaryTrendLedgerRun.v1":
        errors.append("schema_version_mismatch")
    if run.get("authority") != AUTHORITY_FLAGS:
        errors.append("authority_mismatch")
    if not isinstance(run.get("entries"), list):
        errors.append("entries_not_list")
    if not isinstance(run.get("counts"), dict):
        errors.append("counts_not_dict")
    return errors
