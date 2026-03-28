from __future__ import annotations

from abx.observability.falseAssuranceRecords import build_false_assurance_records
from abx.observability.instrumentationFreshnessRecords import build_instrumentation_freshness_records
from abx.observability.observabilityTransitions import build_observability_transition_records
from abx.observability.types import CoverageGovernanceErrorRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_observability_transition_report() -> dict[str, object]:
    transitions = build_observability_transition_records()
    freshness = build_instrumentation_freshness_records()
    assurance = build_false_assurance_records()
    errors = []
    for row in transitions:
        if row.to_state in {"FALSE_ASSURANCE_RISK", "BLOCKED"}:
            errors.append(CoverageGovernanceErrorRecord("OBSERVABILITY_TRANSITION_BLOCKING", "ERROR", f"{row.surface_ref} state={row.to_state}"))
        elif row.to_state in {"PARTIAL_VISIBILITY_ACTIVE", "INSTRUMENTATION_STALE"}:
            errors.append(CoverageGovernanceErrorRecord("OBSERVABILITY_TRANSITION_ATTENTION", "WARN", f"{row.surface_ref} state={row.to_state}"))
    report = {
        "artifactType": "ObservabilityTransitionAudit.v1",
        "artifactId": "observability-transition-audit",
        "transitions": [x.__dict__ for x in transitions],
        "freshness": [x.__dict__ for x in freshness],
        "assurance": [x.__dict__ for x in assurance],
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
