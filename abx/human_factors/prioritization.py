from __future__ import annotations

from abx.human_factors.types import CognitivePriorityRecord


def build_prioritization_records() -> list[CognitivePriorityRecord]:
    return [
        CognitivePriorityRecord("prio.incident.active", "incident", "must_act_now", "critical", "immediate", "operations"),
        CognitivePriorityRecord("prio.integrity.warning", "security_integrity", "should_review", "high", "current_shift", "governance"),
        CognitivePriorityRecord("prio.performance.drift", "performance", "contextual", "medium", "today", "runtime"),
        CognitivePriorityRecord("prio.training.reference", "training", "background", "low", "defer", "operations"),
        CognitivePriorityRecord("prio.archive.history", "archive", "archival_reference", "low", "defer", "governance"),
    ]
