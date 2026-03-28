from __future__ import annotations

from abx.identity.deprecatedIdentifierRecords import build_deprecated_identifier_records
from abx.identity.referenceMismatchRecords import build_reference_mismatch_records
from abx.identity.types import IdentityGovernanceErrorRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_identity_transition_report() -> dict[str, object]:
    mismatches = build_reference_mismatch_records()
    deprecated = build_deprecated_identifier_records()
    errors = []
    for row in mismatches:
        if row.mismatch_state in {"DUPLICATE_CONFIRMED", "REFERENCE_MISMATCH_ACTIVE"}:
            errors.append(IdentityGovernanceErrorRecord("IDENTITY_TRANSITION_FAIL", "ERROR", f"{row.reference_ref} state={row.mismatch_state}"))
        elif row.mismatch_state in {"DUPLICATE_SUSPECTED", "DEPRECATED_IDENTIFIER_ACTIVE", "REMAP_REQUIRED"}:
            errors.append(IdentityGovernanceErrorRecord("IDENTITY_TRANSITION_ATTENTION", "WARN", f"{row.reference_ref} state={row.mismatch_state}"))

    report = {
        "artifactType": "IdentityTransitionAudit.v1",
        "artifactId": "identity-transition-audit",
        "mismatch": [x.__dict__ for x in mismatches],
        "deprecated": [x.__dict__ for x in deprecated],
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
