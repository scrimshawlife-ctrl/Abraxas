from __future__ import annotations

from abx.outcome.outcomeTransitions import build_outcome_transition_records
from abx.outcome.types import OutcomeGovernanceErrorRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_outcome_transition_report() -> dict[str, object]:
    rows = build_outcome_transition_records()
    errors = []
    for row in rows:
        if row.verification_state in {"EFFECT_ABSENT", "OUTCOME_CONTRADICTORY", "VERIFICATION_REQUIRED"}:
            errors.append(OutcomeGovernanceErrorRecord("OUTCOME_TRANSITION_BLOCKING", "ERROR", f"{row.action_ref} state={row.verification_state}"))
        elif row.verification_state in {"EFFECT_PARTIAL", "EFFECT_DELAYED"}:
            errors.append(OutcomeGovernanceErrorRecord("OUTCOME_TRANSITION_ATTENTION", "WARN", f"{row.action_ref} state={row.verification_state}"))
    report = {
        "artifactType": "OutcomeTransitionAudit.v1",
        "artifactId": "outcome-transition-audit",
        "transitions": [x.__dict__ for x in rows],
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
