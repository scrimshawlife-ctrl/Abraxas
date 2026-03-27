from __future__ import annotations

from abx.lineage.lineageClassification import classify_lineage
from abx.lineage.lineageRecords import build_lineage_records
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_lineage_report() -> dict[str, object]:
    rows = build_lineage_records()
    states = {row.lineage_id: classify_lineage(lineage_kind=row.lineage_kind, source_ref=row.source_ref) for row in rows}
    report = {
        "artifactType": "LineageAudit.v1",
        "artifactId": "lineage-audit",
        "lineage": [x.__dict__ for x in rows],
        "lineageStates": states,
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
