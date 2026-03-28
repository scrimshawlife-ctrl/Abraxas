from __future__ import annotations

from abx.lineage.provenanceTransitions import build_provenance_transition_records
from abx.lineage.replayabilityRecords import build_replayability_records
from abx.lineage.types import LineageGovernanceErrorRecord
from abx.lineage.unauthorizedMutationRecords import build_unauthorized_mutation_records
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_provenance_transition_report() -> dict[str, object]:
    transitions = build_provenance_transition_records()
    replay = build_replayability_records()
    unauthorized = build_unauthorized_mutation_records()
    errors = []
    for transition in transitions:
        if transition.to_state in {"PROVENANCE_STALE", "STALE_DERIVED_STATE", "NON_REPLAYABLE_STATE"}:
            errors.append(
                LineageGovernanceErrorRecord(
                    code="PROVENANCE_TRANSITION_DOWNGRADE",
                    severity="WARN",
                    message=f"{transition.state_ref} transitioned to {transition.to_state}",
                )
            )
        if transition.to_state in {"UNAUTHORIZED_MUTATION", "BLOCKED"}:
            errors.append(
                LineageGovernanceErrorRecord(
                    code="PROVENANCE_TRANSITION_CRITICAL",
                    severity="ERROR",
                    message=f"{transition.state_ref} transitioned to {transition.to_state}",
                )
            )
    report = {
        "artifactType": "ProvenanceTransitionAudit.v1",
        "artifactId": "provenance-transition-audit",
        "transitions": [x.__dict__ for x in transitions],
        "replayability": [x.__dict__ for x in replay],
        "unauthorized": [x.__dict__ for x in unauthorized],
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
