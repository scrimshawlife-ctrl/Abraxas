from __future__ import annotations

from abx.failure.failureClassification import classify_failure_semantics
from abx.failure.failureSemantics import build_failure_semantic_inventory
from abx.failure.recoverabilityRecords import build_recoverability_records
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_failure_semantics_report() -> dict[str, object]:
    rows = build_failure_semantic_inventory()
    semantics = {
        x.semantic_id: classify_failure_semantics(
            recoverability=x.recoverability,
            degraded_state=x.degraded_state,
            integrity_impact=x.integrity_impact,
        )
        for x in rows
    }
    report = {
        "artifactType": "FailureSemanticsAudit.v1",
        "artifactId": "failure-semantics-audit",
        "semantics": [x.__dict__ for x in rows],
        "semanticStates": semantics,
        "recoverability": [x.__dict__ for x in build_recoverability_records()],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
