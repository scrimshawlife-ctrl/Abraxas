from __future__ import annotations

from typing import Any, Mapping

from abraxas.canary.rollback_observation_ledger import build_rollback_observation_ledger
from abraxas.canary.rollback_observation_validator import validate_rollback_observation_ledger


def run_rollback_observation_ledger(
    execution_run: Mapping[str, Any],
    prior_ledger: Mapping[str, Any] | None = None,
) -> dict:
    report = build_rollback_observation_ledger(execution_run, prior_ledger)
    errors = validate_rollback_observation_ledger(report)
    if errors:
        raise ValueError(";".join(errors))
    return report
