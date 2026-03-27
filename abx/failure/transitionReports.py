from __future__ import annotations

from abx.failure.failureTransitions import build_failure_transition_records
from abx.failure.integrityRiskRecords import build_integrity_risk_records
from abx.failure.unsafeRestorationRecords import build_unsafe_restoration_records
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_failure_transition_report() -> dict[str, object]:
    transitions = build_failure_transition_records()
    integrity = build_integrity_risk_records()
    unsafe = build_unsafe_restoration_records()
    report = {
        "artifactType": "FailureTransitionAudit.v1",
        "artifactId": "failure-transition-audit",
        "transitions": [x.__dict__ for x in transitions],
        "integrityRisk": [x.__dict__ for x in integrity],
        "unsafeRestoration": [x.__dict__ for x in unsafe],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
