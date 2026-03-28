from __future__ import annotations

from abx.operator.operatorTraceRecords import build_operator_trace_records
from abx.operator.traceClassification import (
    classify_reason_quality,
    classify_reversibility,
    classify_scope,
    classify_trace_completeness,
)
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_traceability_report() -> dict[str, object]:
    traces = build_operator_trace_records()
    completeness = {x.trace_id: classify_trace_completeness(x) for x in traces}
    reason = {x.trace_id: classify_reason_quality(x) for x in traces}
    scopes = [classify_scope(x).__dict__ for x in traces]
    reversibility = [classify_reversibility(x).__dict__ for x in traces]
    report = {
        "artifactType": "OperatorTraceabilityAudit.v1",
        "artifactId": "operator-traceability-audit",
        "traces": [x.__dict__ for x in traces],
        "traceCompleteness": completeness,
        "reasonQuality": reason,
        "scopeRecords": scopes,
        "reversibilityRecords": reversibility,
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
