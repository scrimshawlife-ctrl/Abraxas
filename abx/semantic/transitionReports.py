from __future__ import annotations

from abx.semantic.deprecatedMeaningRecords import build_deprecated_meaning_records
from abx.semantic.semanticAliasRecords import build_semantic_alias_records
from abx.semantic.semanticTransitions import build_semantic_transition_records
from abx.semantic.types import SemanticGovernanceErrorRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_semantic_transition_report() -> dict[str, object]:
    transitions = build_semantic_transition_records()
    alias = build_semantic_alias_records()
    deprecated = build_deprecated_meaning_records()
    errors = []
    for transition in transitions:
        if transition.to_state in {"ALIAS_DRIFT_DETECTED", "STRUCTURALLY_COMPATIBLE_BUT_SEMANTICALLY_SHIFTED"}:
            errors.append(SemanticGovernanceErrorRecord("SEMANTIC_TRANSITION_WARN", "WARN", f"{transition.entity_ref} to={transition.to_state}"))
        if transition.to_state in {"BLOCKED", "SEMANTIC_BREAK"}:
            errors.append(SemanticGovernanceErrorRecord("SEMANTIC_TRANSITION_BLOCKED", "ERROR", f"{transition.entity_ref} to={transition.to_state}"))
    report = {
        "artifactType": "SemanticTransitionAudit.v1",
        "artifactId": "semantic-transition-audit",
        "transitions": [x.__dict__ for x in transitions],
        "aliases": [x.__dict__ for x in alias],
        "deprecated": [x.__dict__ for x in deprecated],
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
