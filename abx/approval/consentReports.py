from __future__ import annotations

from abx.approval.consentClassification import classify_consent_state
from abx.approval.consentStateRecords import build_consent_state_records
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_consent_state_report() -> dict[str, object]:
    records = build_consent_state_records()
    states = {row.consent_id: classify_consent_state(row.consent_state) for row in records}
    report = {
        "artifactType": "ConsentStateAudit.v1",
        "artifactId": "consent-state-audit",
        "consentStates": [x.__dict__ for x in records],
        "consentClassification": states,
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
