from __future__ import annotations

from abx.outcome.intendedOutcomeClassification import classify_intended_outcome
from abx.outcome.intendedOutcomeRecords import build_intended_outcome_records
from abx.outcome.types import OutcomeGovernanceErrorRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_intended_outcome_report() -> dict[str, object]:
    rows = build_intended_outcome_records()
    states = {x.outcome_id: classify_intended_outcome(intended_state=x.intended_state) for x in rows}
    errors = []
    for row in rows:
        state = states[row.outcome_id]
        if state == "OUTCOME_UNKNOWN":
            errors.append(OutcomeGovernanceErrorRecord("INTENDED_OUTCOME_UNKNOWN", "ERROR", f"{row.action_ref} state={state}"))
        elif state in {"SIDE_EFFECT", "DOWNSTREAM_EFFECT"}:
            errors.append(OutcomeGovernanceErrorRecord("INTENDED_OUTCOME_ATTENTION", "WARN", f"{row.action_ref} state={state}"))
    report = {
        "artifactType": "IntendedOutcomeAudit.v1",
        "artifactId": "intended-outcome-audit",
        "intended": [x.__dict__ for x in rows],
        "intendedStates": states,
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
