from __future__ import annotations

from typing import Any, Mapping

from abraxas.canary.activation_executor import build_canary_activation_execution_run
from abraxas.canary.execution_validator import validate_execution_run


def run_activation_executor(
    activation_packet_run: Mapping[str, Any],
    *,
    created_at: str,
    scope_id: str,
    sandbox_root: str | None = None,
) -> dict:
    report = build_canary_activation_execution_run(
        activation_packet_run,
        created_at=created_at,
        scope_id=scope_id,
        sandbox_root=sandbox_root,
    )
    errors = validate_execution_run(report)
    report["validation"] = {"valid": len(errors) == 0 and report.get("validation", {}).get("valid", False), "errors": sorted(set(report.get("validation", {}).get("errors", []) + errors))}
    return report
