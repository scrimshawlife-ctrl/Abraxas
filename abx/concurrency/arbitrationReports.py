from __future__ import annotations

from abx.concurrency.arbitrationPolicies import build_arbitration_policies
from abx.concurrency.arbitrationRecords import build_arbitration_decisions
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_arbitration_report() -> dict[str, object]:
    policies = build_arbitration_policies()
    decisions = build_arbitration_decisions()
    report = {
        "artifactType": "ArbitrationAudit.v1",
        "artifactId": "arbitration-audit",
        "policies": [x.__dict__ for x in policies],
        "decisions": [x.__dict__ for x in decisions],
        "outcomes": {
            k: sorted(x.decision_id for x in decisions if x.outcome == k)
            for k in sorted({x.outcome for x in decisions})
        },
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
