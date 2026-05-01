from __future__ import annotations

from typing import Any, Mapping

from abraxas.canary.rollback_packet import build_rollback_packet_run
from abraxas.canary.rollback_packet_validator import validate_rollback_packet_run


def run_rollback_packet(
    review_run: Mapping[str, Any],
    rollback_prep_run: Mapping[str, Any],
    observation_run: Mapping[str, Any],
) -> dict:
    report = build_rollback_packet_run(review_run, rollback_prep_run, observation_run)
    errors = validate_rollback_packet_run(report)
    if errors:
        raise ValueError(";".join(errors))
    return report
