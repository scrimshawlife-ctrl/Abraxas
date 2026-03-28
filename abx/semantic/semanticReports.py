from __future__ import annotations

from abx.semantic.semanticClassification import classify_semantic_drift
from abx.semantic.semanticDriftRecords import build_semantic_drift_records
from abx.semantic.types import SemanticGovernanceErrorRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_semantic_drift_report() -> dict[str, object]:
    rows = build_semantic_drift_records()
    states = {x.drift_id: classify_semantic_drift(drift_state=x.drift_state, drift_kind=x.drift_kind) for x in rows}
    errors = []
    for row in rows:
        state = states[row.drift_id]
        if state in {"SEMANTIC_DRIFT_DETECTED", "SEMANTIC_BREAK"}:
            errors.append(SemanticGovernanceErrorRecord("SEMANTIC_DRIFT_DETECTED", "ERROR", f"{row.entity_ref} drift={state}"))
        elif state in {"SEMANTIC_ALIAS_ACTIVE", "SEMANTIC_DEPRECATION_ACTIVE", "NOT_COMPUTABLE"}:
            errors.append(SemanticGovernanceErrorRecord("SEMANTIC_ATTENTION_REQUIRED", "WARN", f"{row.entity_ref} drift={state}"))
    report = {
        "artifactType": "SemanticDriftAudit.v1",
        "artifactId": "semantic-drift-audit",
        "semantic": [x.__dict__ for x in rows],
        "semanticStates": states,
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
