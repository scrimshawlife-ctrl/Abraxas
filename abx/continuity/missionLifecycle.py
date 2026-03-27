from __future__ import annotations

from abx.continuity.types import MissionLifecycleRecord


def build_mission_lifecycle_records() -> list[MissionLifecycleRecord]:
    rows = [
        MissionLifecycleRecord("lifecycle.governance-closure", "mission.governance-closure", "ACTIVE", "plan.pass28-closure", []),
        MissionLifecycleRecord("lifecycle.bounded-agency", "mission.bounded-agency", "PAUSED", "plan.pass29-agency", ["operator_window_shift"]),
        MissionLifecycleRecord("lifecycle.concurrent-arbitration", "mission.concurrent-arbitration", "INITIATED", "plan.pass30-concurrency", []),
        MissionLifecycleRecord("lifecycle.wave6-legacy", "mission.wave6-legacy", "SUPERSEDED", "plan.legacy-wave6", ["canon_replacement"]),
        MissionLifecycleRecord("lifecycle.ops-cleanup", "mission.ops-cleanup", "RETIRED", "plan.ops-retired", []),
    ]
    return sorted(rows, key=lambda x: x.lifecycle_id)
