from __future__ import annotations

from abx.semantic.meaningPreservation import build_meaning_preservation_records
from abx.semantic.migrationClassification import classify_meaning_preservation
from abx.semantic.reinterpretationRisk import build_reinterpretation_risk_records
from abx.semantic.types import SemanticGovernanceErrorRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_meaning_preservation_report() -> dict[str, object]:
    meaning = build_meaning_preservation_records()
    risk = build_reinterpretation_risk_records()
    states = {
        x.preservation_id: classify_meaning_preservation(
            preservation_state=x.preservation_state,
            migration_state=x.migration_state,
            translation_required=x.translation_required,
        )
        for x in meaning
    }
    errors = []
    for record in meaning:
        state = states[record.preservation_id]
        if state in {"SEMANTIC_BREAK", "MIGRATION_REQUIRED"}:
            errors.append(SemanticGovernanceErrorRecord("MEANING_PRESERVATION_FAIL", "ERROR", f"{record.entity_ref} state={state}"))
    report = {
        "artifactType": "MeaningPreservationAudit.v1",
        "artifactId": "meaning-preservation-audit",
        "meaning": [x.__dict__ for x in meaning],
        "reinterpretationRisk": [x.__dict__ for x in risk],
        "meaningStates": states,
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
