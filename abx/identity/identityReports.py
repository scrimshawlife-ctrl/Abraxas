from __future__ import annotations

from abx.identity.identityClassification import classify_identity_resolution
from abx.identity.identityResolutionRecords import build_identity_resolution_records
from abx.identity.types import IdentityGovernanceErrorRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_identity_resolution_report() -> dict[str, object]:
    rows = build_identity_resolution_records()
    states = {x.resolution_id: classify_identity_resolution(resolution_state=x.resolution_state, canonical_entity=x.canonical_entity) for x in rows}
    errors = []
    for row in rows:
        state = states[row.resolution_id]
        if state in {"REFERENTIAL_MISMATCH", "BLOCKED", "UNRESOLVED_REFERENCE"}:
            errors.append(IdentityGovernanceErrorRecord("IDENTITY_RESOLUTION_FAIL", "ERROR", f"{row.reference_ref} state={state}"))
        elif state in {"REFERENCE_AMBIGUOUS", "NOT_COMPUTABLE", "ALIAS_RESOLVED"}:
            errors.append(IdentityGovernanceErrorRecord("IDENTITY_RESOLUTION_ATTENTION", "WARN", f"{row.reference_ref} state={state}"))

    report = {
        "artifactType": "IdentityResolutionAudit.v1",
        "artifactId": "identity-resolution-audit",
        "identity": [x.__dict__ for x in rows],
        "identityStates": states,
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
