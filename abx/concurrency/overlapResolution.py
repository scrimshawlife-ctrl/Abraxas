from __future__ import annotations

from abx.concurrency.arbitrationRecords import build_arbitration_decisions
from abx.concurrency.types import CompensationRecord, OverlapResolutionRecord


def build_overlap_resolution_records() -> list[OverlapResolutionRecord]:
    rows: list[OverlapResolutionRecord] = []
    for row in build_arbitration_decisions():
        if row.outcome == "MERGED":
            outcome_class = "MERGED"
            mode = "parallel-safe"
            safety = "CONTROLLED"
        elif row.outcome == "SERIALIZED":
            outcome_class = "SERIALIZED"
            mode = "serialized"
            safety = "CONTROLLED"
        elif row.outcome == "DELAYED":
            outcome_class = "DELAYED"
            mode = "backoff"
            safety = "DEGRADED"
        elif row.outcome == "ESCALATED":
            outcome_class = "YIELDED"
            mode = "human-arbitration"
            safety = "DEGRADED"
        elif row.outcome in {"DENIED", "BLOCKED"}:
            outcome_class = "ABORTED"
            mode = "suppressed"
            safety = "BLOCKED"
        else:
            outcome_class = "NOT_COMPUTABLE"
            mode = "unknown"
            safety = "NOT_COMPUTABLE"
        rows.append(
            OverlapResolutionRecord(
                resolution_id=f"resolution.{row.decision_id}",
                conflict_id=row.conflict_id,
                outcome_class=outcome_class,
                execution_mode=mode,
                safety_state=safety,
            )
        )
    return sorted(rows, key=lambda x: x.resolution_id)


def build_compensation_records() -> list[CompensationRecord]:
    rows: list[CompensationRecord] = []
    for row in build_overlap_resolution_records():
        requires = row.outcome_class in {"ABORTED", "NOT_COMPUTABLE"}
        comp_class = "COMPENSATED" if requires else "NONE"
        reason = "prevent_partial_side_effect_drift" if requires else "no_compensation_required"
        rows.append(
            CompensationRecord(
                compensation_id=f"comp.{row.resolution_id}",
                conflict_id=row.conflict_id,
                compensation_class=comp_class,
                required=requires,
                reason=reason,
            )
        )
    return sorted(rows, key=lambda x: x.compensation_id)
