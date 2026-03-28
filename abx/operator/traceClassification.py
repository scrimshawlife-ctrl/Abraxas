from __future__ import annotations

from abx.operator.types import InterventionScopeRecord, OperatorTraceRecord, ReversibilityRecord


def classify_trace_completeness(record: OperatorTraceRecord) -> str:
    return "TRACE_COMPLETE" if record.trace_state_signal == "complete" else "TRACE_PARTIAL"


def classify_reason_quality(record: OperatorTraceRecord) -> str:
    return "REASON_EXPLICIT" if len(record.reason_text.strip()) >= 16 else "REASON_INSUFFICIENT"


def classify_scope(record: OperatorTraceRecord) -> InterventionScopeRecord:
    state = "SCOPE_OVERBROAD" if "all-tenants" in record.scope_ref or "global" in record.scope_ref else "SCOPE_BOUNDED"
    rationale = "Global or tenant-wide mutation exceeds local intervention boundary" if state == "SCOPE_OVERBROAD" else "Scope maps to bounded intervention surface"
    return InterventionScopeRecord(
        scope_id=f"scp.{record.trace_id}",
        intervention_id=record.intervention_id,
        scope_state=state,
        rationale=rationale,
    )


def classify_reversibility(record: OperatorTraceRecord) -> ReversibilityRecord:
    if record.reversibility_signal == "reversible":
        state = "REVERSIBLE"
        restoration_required = "NO"
    elif record.reversibility_signal == "restoration-required":
        state = "REVERSIBLE"
        restoration_required = "YES"
    else:
        state = "NON_REVERSIBLE"
        restoration_required = "YES"
    return ReversibilityRecord(
        reversibility_id=f"rev.{record.trace_id}",
        intervention_id=record.intervention_id,
        reversibility_state=state,
        restoration_required=restoration_required,
    )
