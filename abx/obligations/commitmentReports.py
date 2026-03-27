from __future__ import annotations

from abx.obligations.commitmentClassification import classify_commitment_state
from abx.obligations.externalCommitmentRecords import build_external_commitment_records
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_external_commitment_report() -> dict[str, object]:
    records = build_external_commitment_records()
    states = {row.commitment_id: classify_commitment_state(row.commitment_state) for row in records}
    report = {
        "artifactType": "ExternalCommitmentAudit.v1",
        "artifactId": "external-commitment-audit",
        "commitments": [x.__dict__ for x in records],
        "commitmentStates": states,
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
