from __future__ import annotations

from abx.lineage.lineageClassification import classify_lineage
from abx.lineage.lineageRecords import build_lineage_records
from abx.lineage.types import LineageGovernanceErrorRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_lineage_report() -> dict[str, object]:
    rows = build_lineage_records()
    states = {row.lineage_id: classify_lineage(lineage_kind=row.lineage_kind, source_ref=row.source_ref) for row in rows}
    errors = []
    for row in rows:
        state = states[row.lineage_id]
        if state == "NOT_COMPUTABLE":
            errors.append(
                LineageGovernanceErrorRecord(
                    code="LINEAGE_NOT_COMPUTABLE",
                    severity="ERROR",
                    message=f"{row.state_ref} lineage kind is unsupported: {row.lineage_kind}",
                )
            )
        elif state == "PROVENANCE_BROKEN":
            errors.append(
                LineageGovernanceErrorRecord(
                    code="LINEAGE_BROKEN",
                    severity="ERROR",
                    message=f"{row.state_ref} is missing source traceability",
                )
            )
    report = {
        "artifactType": "LineageAudit.v1",
        "artifactId": "lineage-audit",
        "lineage": [x.__dict__ for x in rows],
        "lineageStates": states,
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
