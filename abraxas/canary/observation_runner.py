from __future__ import annotations

from typing import Any, Mapping

from abraxas.canary.observation_ledger import build_observation_ledger
from abraxas.canary.observation_validator import validate_observation_ledger_run


def run_observation_ledger(
    execution_run: Mapping[str, Any],
    previous_ledger: Mapping[str, Any] | None = None,
) -> dict:
    run = build_observation_ledger(execution_run=execution_run, previous_ledger=previous_ledger)
    errors = validate_observation_ledger_run(run)
    if errors:
        raise ValueError(";".join(errors))
    return run
