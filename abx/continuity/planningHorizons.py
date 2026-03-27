from __future__ import annotations

from abx.continuity.types import PlanningHorizonRecord


def build_planning_horizons() -> list[PlanningHorizonRecord]:
    rows = [
        PlanningHorizonRecord("horizon.governance-closure", "mission.governance-closure", "90d", "weekly-checkpoint", "VIABLE"),
        PlanningHorizonRecord("horizon.bounded-agency", "mission.bounded-agency", "90d", "biweekly-checkpoint", "VIABLE"),
        PlanningHorizonRecord("horizon.concurrent-arbitration", "mission.concurrent-arbitration", "60d", "weekly-checkpoint", "PENDING"),
        PlanningHorizonRecord("horizon.wave6-legacy", "mission.wave6-legacy", "365d", "monthly-checkpoint", "STALE"),
        PlanningHorizonRecord("horizon.ops-cleanup", "mission.ops-cleanup", "30d", "closeout-checkpoint", "RETIRED"),
    ]
    return sorted(rows, key=lambda x: x.horizon_id)
