from __future__ import annotations

from abx.human_factors.cognitiveLoad import build_cognitive_load_inventory
from abx.human_factors.prioritization import build_prioritization_records
from abx.human_factors.salienceClassification import classify_salience, classify_urgency
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_cognitive_load_audit_report() -> dict[str, object]:
    report = {
        "artifactType": "CognitiveLoadAudit.v1",
        "artifactId": "cognitive-load-audit",
        "cognitiveLoad": [x.__dict__ for x in build_cognitive_load_inventory()],
        "prioritization": [x.__dict__ for x in build_prioritization_records()],
        "salienceClassification": classify_salience(),
        "urgencyClassification": classify_urgency(),
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
