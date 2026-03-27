from __future__ import annotations

from abx.continuity.missionLifecycle import build_mission_lifecycle_records
from abx.continuity.types import RetirementRecord


def build_retirement_records() -> list[RetirementRecord]:
    rows = [
        RetirementRecord(
            retirement_id=f"retirement.{row.mission_id}",
            mission_id=row.mission_id,
            retirement_state="ARCHIVED" if row.lifecycle_state == "RETIRED" else "ACTIVE_ARCHIVE",
            archive_ref=row.evidence_ref,
        )
        for row in build_mission_lifecycle_records()
        if row.lifecycle_state == "RETIRED"
    ]
    return sorted(rows, key=lambda x: x.retirement_id)
