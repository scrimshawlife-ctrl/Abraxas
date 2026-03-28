from __future__ import annotations

from abx.tradeoff.types import PriorityAssignmentRecord


def build_priority_inventory() -> tuple[PriorityAssignmentRecord, ...]:
    return (
        PriorityAssignmentRecord("pri.release", "release.deploy", "CANON_PRIORITY", 1, "policy_order"),
        PriorityAssignmentRecord("pri.queue", "scheduler.dispatch", "SITUATIONAL_PRIORITY", 1, "latency_first"),
        PriorityAssignmentRecord("pri.incident", "incident.response", "EMERGENCY_PRIORITY_OVERRIDE", 1, "incident_severity"),
        PriorityAssignmentRecord("pri.defer", "obligation.triage", "TEMPORARY_PRIORITY_OVERRIDE", 2, "deadline_window"),
        PriorityAssignmentRecord("pri.tie", "operator.routing", "TIE_BREAK_PRIORITY", 3, "operator_load"),
        PriorityAssignmentRecord("pri.legacy", "legacy.dispatch", "PRIORITY_UNKNOWN", 99, "unknown"),
    )
