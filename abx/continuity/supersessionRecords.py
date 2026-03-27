from __future__ import annotations

from abx.continuity.continuityLineage import build_continuity_lineage_records
from abx.continuity.types import SupersessionRecord


def build_supersession_records() -> list[SupersessionRecord]:
    rows = [
        SupersessionRecord(
            supersession_id=f"supersession.{row.mission_id}",
            mission_id=row.mission_id,
            superseded_by=row.supersedes,
            reason="canonical_replacement" if row.supersedes else "not_superseded",
        )
        for row in build_continuity_lineage_records()
        if row.supersedes
    ]
    return sorted(rows, key=lambda x: x.supersession_id)
