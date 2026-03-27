from __future__ import annotations

from abx.knowledge.types import ContinuityRecord


def build_continuity_inventory(run_id: str = "RUN-CONTINUITY") -> list[ContinuityRecord]:
    rows = [
        ContinuityRecord(
            continuity_id=f"continuity.{run_id}.direct",
            run_id=run_id,
            previous_ref=f"{run_id}-PREV",
            baseline_ref="BASELINE-V1",
            incident_ref=None,
            linkage_type="direct",
        ),
        ContinuityRecord(
            continuity_id=f"continuity.{run_id}.derived",
            run_id=run_id,
            previous_ref=f"{run_id}-PREV",
            baseline_ref="BASELINE-V1",
            incident_ref="inc.none",
            linkage_type="derived",
        ),
    ]
    return rows
