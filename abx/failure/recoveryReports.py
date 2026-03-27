from __future__ import annotations

from abx.failure.recoveryActions import build_recovery_action_records
from abx.failure.recoveryClassification import classify_recovery
from abx.failure.recoveryEligibility import build_recovery_eligibility_inventory
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_recovery_eligibility_report() -> dict[str, object]:
    eligibility = build_recovery_eligibility_inventory()
    states = {
        row.eligibility_id: classify_recovery(
            retry_allowed=row.retry_allowed,
            restore_allowed=row.restore_allowed,
            clearance_required=row.clearance_required,
        )
        for row in eligibility
    }
    report = {
        "artifactType": "RecoveryEligibilityAudit.v1",
        "artifactId": "recovery-eligibility-audit",
        "eligibility": [x.__dict__ for x in eligibility],
        "recoveryStates": states,
        "actions": [x.__dict__ for x in build_recovery_action_records()],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
