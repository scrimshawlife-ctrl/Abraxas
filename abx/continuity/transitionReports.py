from __future__ import annotations

from abx.continuity.retirementRecords import build_retirement_records
from abx.continuity.supersessionRecords import build_supersession_records
from abx.continuity.transitionRecords import build_transition_records
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_continuity_transition_report() -> dict[str, object]:
    transitions = build_transition_records()
    supersessions = build_supersession_records()
    retirements = build_retirement_records()
    report = {
        "artifactType": "MissionTransitionAudit.v1",
        "artifactId": "mission-transition-audit",
        "transitions": [x.__dict__ for x in transitions],
        "supersessions": [x.__dict__ for x in supersessions],
        "retirements": [x.__dict__ for x in retirements],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
