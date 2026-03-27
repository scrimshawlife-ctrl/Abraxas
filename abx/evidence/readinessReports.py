from __future__ import annotations

from abx.evidence.readinessClassification import classify_readiness
from abx.evidence.sufficiencyReports import build_sufficiency_report
from abx.evidence.thresholdReports import build_threshold_report
from abx.evidence.types import DecisionReadinessRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_readiness_report() -> dict[str, object]:
    threshold = build_threshold_report()
    consequence = {x["decision_class"]: x["consequence_level"] for x in threshold["thresholds"]}
    sufficiency = build_sufficiency_report()
    readiness = tuple(
        DecisionReadinessRecord(
            readiness_id=f"ready.{row['decision_class'].lower()}",
            decision_class=row["decision_class"],
            readiness_state=classify_readiness(sufficiency_state=row["sufficiency_state"], consequence_level=consequence[row["decision_class"]]),
            readiness_reason=row["sufficiency_state"].lower(),
        )
        for row in sufficiency["sufficiency"]
    )
    report = {
        "artifactType": "DecisionReadinessAudit.v1",
        "artifactId": "decision-readiness-audit",
        "readiness": [x.__dict__ for x in readiness],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
