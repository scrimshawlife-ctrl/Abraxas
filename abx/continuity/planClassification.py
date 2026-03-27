from __future__ import annotations


PLAN_STATES = {
    "ACTIVE_MISSION",
    "STAGED_PLAN",
    "PAUSED_CONTINUITY",
    "RESUMABLE_CONTINUITY",
    "BRANCHED_CONTINUITY",
    "SUPERSEDED_CONTINUITY",
    "STALE_CONTINUITY",
    "RETIRED_MISSION",
    "BLOCKED",
    "DEGRADED",
    "NOT_COMPUTABLE",
}


def classify_plan_state(*, plan_state: str, viability_state: str) -> str:
    if plan_state not in PLAN_STATES:
        return "NOT_COMPUTABLE"
    if viability_state == "STALE" and plan_state not in {"SUPERSEDED_CONTINUITY", "RETIRED_MISSION"}:
        return "STALE_CONTINUITY"
    if viability_state == "PENDING" and plan_state == "ACTIVE_MISSION":
        return "DEGRADED"
    return plan_state
