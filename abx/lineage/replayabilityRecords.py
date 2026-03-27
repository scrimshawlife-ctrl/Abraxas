from __future__ import annotations

from abx.lineage.types import ReplayabilityRecord


def build_replayability_records() -> tuple[ReplayabilityRecord, ...]:
    return (
        ReplayabilityRecord("rep.rollup", "state.rev.rollup", "REPLAYABLE_STATE", "RECONSTRUCTABLE"),
        ReplayabilityRecord("rep.partner", "state.partner.merged", "NON_REPLAYABLE_STATE", "NON_RECONSTRUCTABLE"),
    )
