from __future__ import annotations

from abx.governance.valueClassification import classify_values, detect_overlapping_value_terms
from abx.governance.valueModel import build_value_model
from abx.governance.valueOwnership import value_ownership_report
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_value_audit_report() -> dict[str, object]:
    report = {
        "artifactType": "ValueModelAudit.v1",
        "artifactId": "value-model-audit",
        "values": [x.__dict__ for x in build_value_model()],
        "classification": classify_values(),
        "ownership": value_ownership_report(),
        "overlaps": detect_overlapping_value_terms(),
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
