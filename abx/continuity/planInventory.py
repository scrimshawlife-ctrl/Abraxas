from __future__ import annotations

from abx.continuity.types import LongHorizonPlanRecord


def build_plan_inventory() -> list[LongHorizonPlanRecord]:
    rows = [
        LongHorizonPlanRecord("plan.pass28-closure", "mission.governance-closure", "ACTIVE_MISSION", "thread.governance-hardening", "QUARTER"),
        LongHorizonPlanRecord("plan.pass29-agency", "mission.bounded-agency", "RESUMABLE_CONTINUITY", "thread.agency-controls", "QUARTER"),
        LongHorizonPlanRecord("plan.pass30-concurrency", "mission.concurrent-arbitration", "STAGED_PLAN", "thread.concurrent-controls", "MID_TERM"),
        LongHorizonPlanRecord("plan.legacy-wave6", "mission.wave6-legacy", "SUPERSEDED_CONTINUITY", "thread.legacy-governance", "LONG_ARC"),
        LongHorizonPlanRecord("plan.ops-retired", "mission.ops-cleanup", "RETIRED_MISSION", "thread.cleanup", "MID_TERM"),
    ]
    return sorted(rows, key=lambda x: x.plan_id)
