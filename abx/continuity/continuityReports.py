from __future__ import annotations

from abx.continuity.continuityClassification import classify_mission_continuity_state
from abx.continuity.continuityLineage import build_continuity_lineage_records
from abx.continuity.missionLifecycle import build_mission_lifecycle_records
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_mission_continuity_report() -> dict[str, object]:
    lifecycle = build_mission_lifecycle_records()
    lineage = build_continuity_lineage_records()
    states = {
        row.mission_id: classify_mission_continuity_state(row.lifecycle_state, row.changed_conditions)
        for row in lifecycle
    }
    report = {
        "artifactType": "MissionContinuityAudit.v1",
        "artifactId": "mission-continuity-audit",
        "lifecycle": [x.__dict__ for x in lifecycle],
        "lineage": [x.__dict__ for x in lineage],
        "missionStates": states,
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
