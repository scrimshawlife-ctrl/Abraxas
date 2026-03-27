from __future__ import annotations

from abx.closure.ratificationCriteria import build_ratification_criteria
from abx.closure.ratificationRecords import build_ratification_decision_record
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_ratification_report() -> dict[str, object]:
    report = {
        "artifactType": "RatificationReport.v1",
        "artifactId": "ratification-report",
        "criteria": [x.__dict__ for x in build_ratification_criteria()],
        "decision": build_ratification_decision_record().__dict__,
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
