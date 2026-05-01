from __future__ import annotations

from typing import Any, Mapping

from abraxas.canary.rollback_prep import build_rollback_prep
from abraxas.canary.rollback_validator import validate_rollback_prep_run


def run_rollback_prep(observation_run: Mapping[str, Any]) -> dict:
    report = build_rollback_prep(observation_run)
    errors = validate_rollback_prep_run(report)
    if errors:
        raise ValueError(";".join(errors))
    return report
