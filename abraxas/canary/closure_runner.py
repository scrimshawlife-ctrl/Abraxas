from __future__ import annotations

from typing import Any, Mapping

from abraxas.canary.closure_validator import validate_cycle_closure_report
from abraxas.canary.cycle_closure import build_cycle_closure_report


def run_cycle_closure_report(
    forward_observations: Mapping[str, Any],
    rollback_observations: Mapping[str, Any],
    forward_executions: Mapping[str, Any],
    rollback_executions: Mapping[str, Any],
) -> dict:
    report = build_cycle_closure_report(
        forward_observations=forward_observations,
        rollback_observations=rollback_observations,
        forward_executions=forward_executions,
        rollback_executions=rollback_executions,
    )
    errors = validate_cycle_closure_report(report)
    if errors:
        raise ValueError(";".join(errors))
    return report
