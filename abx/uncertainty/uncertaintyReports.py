from __future__ import annotations

from abx.uncertainty.uncertaintyClassification import classify_uncertainty
from abx.uncertainty.uncertaintyRecords import build_uncertainty_records
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_uncertainty_report() -> dict[str, object]:
    rows = build_uncertainty_records()
    states = {
        row.uncertainty_id: classify_uncertainty(uncertainty_level=row.uncertainty_level, downgrade_required=row.downgrade_required)
        for row in rows
    }
    report = {
        "artifactType": "UncertaintyAudit.v1",
        "artifactId": "uncertainty-audit",
        "uncertainty": [x.__dict__ for x in rows],
        "uncertaintyStates": states,
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
