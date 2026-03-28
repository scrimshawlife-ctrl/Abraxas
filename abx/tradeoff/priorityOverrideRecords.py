from __future__ import annotations

from abx.tradeoff.types import PriorityOverrideRecord


def build_priority_override_records() -> tuple[PriorityOverrideRecord, ...]:
    return (
        PriorityOverrideRecord("ovr.incident", "incident.response", "EMERGENCY_PRIORITY_OVERRIDE", "sev1_containment"),
        PriorityOverrideRecord("ovr.defer", "obligation.triage", "TEMPORARY_PRIORITY_OVERRIDE", "quarterly_deadline_window"),
        PriorityOverrideRecord("ovr.sticky", "incident.response", "STICKY_OVERRIDE_DETECTED", "override_ttl_expired"),
    )
