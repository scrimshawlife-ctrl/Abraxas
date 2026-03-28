from __future__ import annotations

from abx.freshness.expiryRecords import build_expiry_records
from abx.freshness.freshnessTransitions import build_freshness_transition_records
from abx.freshness.staleSupportRecords import build_stale_support_records
from abx.freshness.types import FreshnessGovernanceErrorRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_freshness_transition_report() -> dict[str, object]:
    transitions = build_freshness_transition_records()
    support = build_stale_support_records()
    expiry = build_expiry_records()

    errors = []
    for row in transitions:
        if row.to_state in {"REUSE_BLOCKED", "REFRESH_OVERDUE"}:
            errors.append(FreshnessGovernanceErrorRecord("FRESHNESS_TRANSITION_BLOCK", "ERROR", f"{row.entity_ref} to={row.to_state}"))
        elif row.to_state in {"STALE_SUPPORT_ACTIVE", "REFRESH_REQUIRED", "ARCHIVAL_DOWNGRADE_ACTIVE"}:
            errors.append(FreshnessGovernanceErrorRecord("FRESHNESS_TRANSITION_ATTENTION", "WARN", f"{row.entity_ref} to={row.to_state}"))

    report = {
        "artifactType": "FreshnessTransitionAudit.v1",
        "artifactId": "freshness-transition-audit",
        "transitions": [x.__dict__ for x in transitions],
        "staleSupport": [x.__dict__ for x in support],
        "expiry": [x.__dict__ for x in expiry],
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
