from __future__ import annotations

from abx.meta.changeClassification import classify_governance_changes, detect_change_taxonomy_drift, detect_hidden_meta_change
from abx.meta.governanceChanges import build_governance_change_inventory
from abx.meta.selfModification import build_self_modification_records
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_governance_change_audit_report() -> dict[str, object]:
    report = {
        "artifactType": "GovernanceChangeAudit.v1",
        "artifactId": "governance-change-audit",
        "changes": [x.__dict__ for x in build_governance_change_inventory()],
        "selfModification": [x.__dict__ for x in build_self_modification_records()],
        "classification": classify_governance_changes(),
        "taxonomyDrift": detect_change_taxonomy_drift(),
        "hiddenMetaChange": detect_hidden_meta_change(),
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
