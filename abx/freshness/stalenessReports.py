from __future__ import annotations

from abx.freshness.archivalValidityRecords import build_archival_validity_records
from abx.freshness.stalenessRecords import build_staleness_records
from abx.freshness.types import FreshnessGovernanceErrorRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_staleness_report() -> dict[str, object]:
    staleness = build_staleness_records()
    archival = build_archival_validity_records()

    errors = []
    for row in staleness:
        if row.staleness_state in {"EXPIRED_FOR_OPERATIONAL_USE", "STALE_SUPPORT_ACTIVE"}:
            errors.append(FreshnessGovernanceErrorRecord("STALENESS_OPERATIONAL_FAIL", "ERROR", f"{row.entity_ref} state={row.staleness_state}"))
        elif row.staleness_state in {"STALE_BUT_VISIBLE", "ARCHIVAL_VALID_ONLY"}:
            errors.append(FreshnessGovernanceErrorRecord("STALENESS_ATTENTION_REQUIRED", "WARN", f"{row.entity_ref} state={row.staleness_state}"))
    for row in archival:
        if row.archival_state == "NOT_COMPUTABLE":
            errors.append(FreshnessGovernanceErrorRecord("ARCHIVAL_VALIDITY_UNKNOWN", "WARN", f"{row.entity_ref} archival={row.archival_state}"))

    report = {
        "artifactType": "StalenessAudit.v1",
        "artifactId": "staleness-audit",
        "staleness": [x.__dict__ for x in staleness],
        "archival": [x.__dict__ for x in archival],
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
