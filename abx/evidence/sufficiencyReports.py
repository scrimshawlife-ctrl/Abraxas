from __future__ import annotations

from abx.evidence.conflictingEvidence import build_conflicting_evidence_records
from abx.evidence.sufficiencyClassification import classify_sufficiency
from abx.evidence.types import DecisionSufficiencyRecord
from abx.evidence.thresholdReports import build_threshold_report
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_sufficiency_report() -> dict[str, object]:
    threshold = build_threshold_report()
    threshold_rows = {x["decision_class"]: x for x in threshold["thresholds"]}
    threshold_by_class = {}
    for tid, state in threshold["thresholdStates"].items():
        decision_class = next(k for k, v in threshold_rows.items() if v["threshold_id"] == tid)
        threshold_by_class[decision_class] = state

    conflicts = {x.decision_class: x.conflict_state for x in build_conflicting_evidence_records()}
    sufficiency = tuple(
        DecisionSufficiencyRecord(
            sufficiency_id=f"suf.{decision_class.lower()}",
            decision_class=decision_class,
            sufficiency_state=classify_sufficiency(threshold_state=state, conflict_state=conflicts.get(decision_class, "NO_CONFLICT")),
            rationale_ref=f"threshold:{decision_class.lower()}",
        )
        for decision_class, state in sorted(threshold_by_class.items())
    )
    report = {
        "artifactType": "BurdenOfProofAudit.v1",
        "artifactId": "burden-of-proof-audit",
        "sufficiency": [x.__dict__ for x in sufficiency],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
