from __future__ import annotations

from abx.obligations.canceledObligations import build_canceled_obligation_records
from abx.obligations.supersededObligations import build_superseded_obligation_records
from abx.obligations.transitionRecords import build_obligation_transition_records
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_obligation_transition_report() -> dict[str, object]:
    transitions = build_obligation_transition_records()
    superseded = build_superseded_obligation_records()
    canceled = build_canceled_obligation_records()
    report = {
        "artifactType": "ObligationTransitionAudit.v1",
        "artifactId": "obligation-transition-audit",
        "transitions": [x.__dict__ for x in transitions],
        "superseded": [x.__dict__ for x in superseded],
        "canceled": [x.__dict__ for x in canceled],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
