from __future__ import annotations

from abx.continuity.missionLifecycle import build_mission_lifecycle_records
from abx.continuity.types import MissionTransitionRecord


DEFAULT_FROM_STATE = {
    "ACTIVE": "INITIATED",
    "PAUSED": "ACTIVE",
    "INITIATED": "STAGED",
    "SUPERSEDED": "ACTIVE",
    "RETIRED": "ACTIVE",
}


def build_transition_records() -> list[MissionTransitionRecord]:
    rows = [
        MissionTransitionRecord(
            transition_id=f"transition.{row.mission_id}",
            mission_id=row.mission_id,
            from_state=DEFAULT_FROM_STATE.get(row.lifecycle_state, "UNKNOWN"),
            to_state=row.lifecycle_state,
            transition_reason=(row.changed_conditions[0] if row.changed_conditions else "steady_progression"),
        )
        for row in build_mission_lifecycle_records()
    ]
    return sorted(rows, key=lambda x: x.transition_id)
