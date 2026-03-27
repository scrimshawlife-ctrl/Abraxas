from __future__ import annotations


def classify_mission_continuity_state(lifecycle_state: str, changed_conditions: list[str]) -> str:
    if lifecycle_state == "ACTIVE":
        return "ACTIVE_MISSION"
    if lifecycle_state == "INITIATED":
        return "STAGED_PLAN"
    if lifecycle_state == "PAUSED":
        return "PAUSED_CONTINUITY"
    if lifecycle_state == "RESUMED":
        return "RESUMABLE_CONTINUITY"
    if lifecycle_state == "BRANCHED":
        return "BRANCHED_CONTINUITY"
    if lifecycle_state == "SUPERSEDED":
        return "SUPERSEDED_CONTINUITY"
    if lifecycle_state == "RETIRED":
        return "RETIRED_MISSION"
    if changed_conditions:
        return "DEGRADED"
    return "NOT_COMPUTABLE"
