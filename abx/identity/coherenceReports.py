from __future__ import annotations

from abx.identity.coherenceClassification import classify_coherence
from abx.identity.referentialCoherenceRecords import build_alias_records, build_merge_records, build_referential_coherence_records, build_split_records
from abx.identity.types import IdentityGovernanceErrorRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_referential_coherence_report() -> dict[str, object]:
    coherence = build_referential_coherence_records()
    alias = build_alias_records()
    merge = build_merge_records()
    split = build_split_records()
    states = {x.coherence_id: classify_coherence(coherence_state=x.coherence_state, downstream_state=x.downstream_state) for x in coherence}

    errors = []
    for row in coherence:
        state = states[row.coherence_id]
        if state in {"DUPLICATE_ENTITY_CONFIRMED", "MERGE_ILLEGITIMATE", "SPLIT_ILLEGITIMATE", "BLOCKED"}:
            errors.append(IdentityGovernanceErrorRecord("COHERENCE_FAIL", "ERROR", f"{row.entity_ref} state={state}"))
        elif state in {"DUPLICATE_ENTITY_SUSPECTED", "MERGE_ACTIVE_COHERENT", "SPLIT_ACTIVE_COHERENT"}:
            errors.append(IdentityGovernanceErrorRecord("COHERENCE_ATTENTION", "WARN", f"{row.entity_ref} state={state}"))

    report = {
        "artifactType": "ReferentialCoherenceAudit.v1",
        "artifactId": "referential-coherence-audit",
        "coherence": [x.__dict__ for x in coherence],
        "alias": [x.__dict__ for x in alias],
        "merge": [x.__dict__ for x in merge],
        "split": [x.__dict__ for x in split],
        "coherenceStates": states,
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
