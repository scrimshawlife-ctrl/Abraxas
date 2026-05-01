from __future__ import annotations

from typing import Any, Mapping

from abraxas.canary.rollback_executor import build_rollback_execution_run
from abraxas.canary.rollback_execution_validator import validate_rollback_execution_run


def run_rollback_executor(
    rollback_packet_run: Mapping[str, Any],
    *,
    created_at: str,
    scope_id: str,
    sandbox_root: str | None = None,
) -> dict:
    report = build_rollback_execution_run(
        rollback_packet_run,
        created_at=created_at,
        scope_id=scope_id,
        sandbox_root=sandbox_root,
    )
    errors = validate_rollback_execution_run(report)
    if errors:
        raise ValueError(";".join(errors))
    return report
