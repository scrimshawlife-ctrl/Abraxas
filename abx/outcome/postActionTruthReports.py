from __future__ import annotations

from abx.outcome.postActionTruthClassification import classify_post_action_truth
from abx.outcome.postActionTruthRecords import build_contradictory_outcome_records, build_post_action_truth_records
from abx.outcome.types import OutcomeGovernanceErrorRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_post_action_truth_report() -> dict[str, object]:
    truth = build_post_action_truth_records()
    contradictory = build_contradictory_outcome_records()
    states = {x.truth_id: classify_post_action_truth(truth_state=x.truth_state) for x in truth}
    errors = []
    for row in truth:
        state = states[row.truth_id]
        if state in {"ABSENT_OUTCOME", "CONTRADICTORY_OUTCOME", "BLOCKED"}:
            errors.append(OutcomeGovernanceErrorRecord("POST_ACTION_TRUTH_BLOCKING", "ERROR", f"{row.action_ref} state={state}"))
        elif state in {"DELAYED_OUTCOME", "PARTIAL_REALIZED_OUTCOME"}:
            errors.append(OutcomeGovernanceErrorRecord("POST_ACTION_TRUTH_ATTENTION", "WARN", f"{row.action_ref} state={state}"))
    report = {
        "artifactType": "PostActionTruthAudit.v1",
        "artifactId": "post-action-truth-audit",
        "truth": [x.__dict__ for x in truth],
        "contradictions": [x.__dict__ for x in contradictory],
        "truthStates": states,
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
