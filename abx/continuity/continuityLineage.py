from __future__ import annotations

from abx.continuity.types import ContinuityLineageRecord


def build_continuity_lineage_records() -> list[ContinuityLineageRecord]:
    rows = [
        ContinuityLineageRecord("lineage.governance-closure", "mission.governance-closure", "mission.governance-baseline", "", ""),
        ContinuityLineageRecord("lineage.bounded-agency", "mission.bounded-agency", "mission.governance-closure", "mission.governance-closure", ""),
        ContinuityLineageRecord("lineage.concurrent-arbitration", "mission.concurrent-arbitration", "mission.bounded-agency", "mission.bounded-agency", ""),
        ContinuityLineageRecord("lineage.wave6-legacy", "mission.wave6-legacy", "mission.wave6-legacy", "", "mission.governance-closure"),
        ContinuityLineageRecord("lineage.ops-cleanup", "mission.ops-cleanup", "mission.ops-cleanup", "", ""),
    ]
    return sorted(rows, key=lambda x: x.lineage_id)
