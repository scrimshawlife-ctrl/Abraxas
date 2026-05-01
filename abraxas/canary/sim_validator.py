from __future__ import annotations

from typing import Any

from abraxas.canary.sim_models import AUTHORITY_FLAGS


def validate_simulation_run(report: dict[str, Any]) -> None:
    if report.get("artifact") != "CANARY-OVERLAY-SIMULATION-001":
        raise ValueError("artifact mismatch")
    if report.get("schema_version") != "CanaryOverlaySimulationRun.v1":
        raise ValueError("schema_version mismatch")
    if report.get("authority") != AUTHORITY_FLAGS:
        raise ValueError("authority flags mismatch")
