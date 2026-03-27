from __future__ import annotations

from abx.approval.authorityClassification import build_approver_validity_records
from abx.approval.authorityToProceed import build_authority_to_proceed_records
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_authority_report() -> dict[str, object]:
    records = build_authority_to_proceed_records()
    validity = build_approver_validity_records(records)
    report = {
        "artifactType": "AuthorityToProceedAudit.v1",
        "artifactId": "authority-to-proceed-audit",
        "authorityRecords": [x.__dict__ for x in records],
        "validityRecords": [x.__dict__ for x in validity],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
