from __future__ import annotations

from abx.docs_governance.handoffClassification import classify_handoff_completeness
from abx.docs_governance.handoffCoverage import build_handoff_coverage
from abx.docs_governance.handoffRecords import build_handoff_records
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_handoff_audit_report() -> dict[str, object]:
    report = {
        "artifactType": "HandoffAudit.v1",
        "artifactId": "handoff-audit",
        "handoffs": [x.__dict__ for x in build_handoff_records()],
        "classification": classify_handoff_completeness(),
        "coverage": [x.__dict__ for x in build_handoff_coverage()],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
