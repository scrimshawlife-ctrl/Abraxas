from __future__ import annotations

from abx.uncertainty.confidenceTransitions import build_confidence_transition_records
from abx.uncertainty.miscalibrationRecords import build_confidence_suppression_records, build_miscalibration_records
from abx.uncertainty.recalibrationTriggers import build_recalibration_trigger_records
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_confidence_transition_report() -> dict[str, object]:
    transitions = build_confidence_transition_records()
    miscalibration = build_miscalibration_records()
    suppression = build_confidence_suppression_records()
    triggers = build_recalibration_trigger_records()
    report = {
        "artifactType": "ConfidenceTransitionAudit.v1",
        "artifactId": "confidence-transition-audit",
        "transitions": [x.__dict__ for x in transitions],
        "miscalibration": [x.__dict__ for x in miscalibration],
        "suppression": [x.__dict__ for x in suppression],
        "recalibration": [x.__dict__ for x in triggers],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
