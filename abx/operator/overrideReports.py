from __future__ import annotations

from abx.operator.humanOverrideRecords import build_human_override_records
from abx.operator.overrideClassification import build_override_state_index, classify_override_legitimacy
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_override_report() -> dict[str, object]:
    records = build_human_override_records()
    state_index = build_override_state_index(records)
    legitimacy = [classify_override_legitimacy(x).__dict__ for x in records]
    report = {
        "artifactType": "HumanOverrideAudit.v1",
        "artifactId": "human-override-audit",
        "overrides": [x.__dict__ for x in records],
        "overrideStates": state_index,
        "legitimacy": legitimacy,
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
