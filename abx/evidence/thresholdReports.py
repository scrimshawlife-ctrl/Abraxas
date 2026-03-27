from __future__ import annotations

from abx.evidence.burdenInventory import build_burden_inventory
from abx.evidence.evidenceThresholdRecords import build_evidence_threshold_records
from abx.evidence.thresholdClassification import classify_threshold_state
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_threshold_report() -> dict[str, object]:
    thresholds = build_evidence_threshold_records()
    burdens = {x.decision_class: x for x in build_burden_inventory()}
    states = {
        row.threshold_id: classify_threshold_state(
            threshold_value=row.threshold_value,
            evidence_strength=burdens[row.decision_class].evidence_strength,
            consequence_level=row.consequence_level,
        )
        for row in thresholds
    }
    report = {
        "artifactType": "EvidenceThresholdAudit.v1",
        "artifactId": "evidence-threshold-audit",
        "thresholds": [x.__dict__ for x in thresholds],
        "thresholdStates": states,
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
