from __future__ import annotations

from abx.identity.canonicalReferenceRecords import build_canonical_reference_records, build_entity_persistence_records
from abx.identity.persistenceClassification import classify_persistence
from abx.identity.types import IdentityGovernanceErrorRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_entity_persistence_report() -> dict[str, object]:
    persistence = build_entity_persistence_records()
    canonical = build_canonical_reference_records()
    states = {x.persistence_id: classify_persistence(persistence_state=x.persistence_state, continuity_ref=x.continuity_ref) for x in persistence}

    errors = []
    for row in persistence:
        state = states[row.persistence_id]
        if state in {"IDENTITY_BREAK", "NOT_COMPUTABLE"}:
            errors.append(IdentityGovernanceErrorRecord("PERSISTENCE_BREAK", "ERROR", f"{row.entity_ref} state={state}"))
        elif state in {"DEPRECATED_IDENTIFIER", "IMPORTED_IDENTITY_SHADOW", "DISPLAY_ALIAS_ONLY", "REMAPPED_CANONICAL_IDENTITY"}:
            errors.append(IdentityGovernanceErrorRecord("PERSISTENCE_ATTENTION", "WARN", f"{row.entity_ref} state={state}"))

    report = {
        "artifactType": "EntityPersistenceAudit.v1",
        "artifactId": "entity-persistence-audit",
        "persistence": [x.__dict__ for x in persistence],
        "canonical": [x.__dict__ for x in canonical],
        "persistenceStates": states,
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
