from __future__ import annotations

from abx.outcome.effectRealizationReports import build_effect_realization_report
from abx.outcome.intendedOutcomeReports import build_intended_outcome_report
from abx.outcome.outcomeTransitionReports import build_outcome_transition_report
from abx.outcome.postActionTruthReports import build_post_action_truth_report
from abx.outcome.types import OutcomeVerificationScorecard
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def _category(*, blocked: bool, contradiction: bool, partial: bool, delayed: bool, not_computable: bool) -> str:
    if not_computable:
        return "NOT_COMPUTABLE"
    if blocked:
        return "BLOCKED"
    if contradiction:
        return "CONTRADICTORY_BURDENED"
    if delayed:
        return "DELAYED_BURDENED"
    if partial:
        return "PARTIAL"
    return "OUTCOME_VERIFIED"


def build_outcome_verification_scorecard() -> OutcomeVerificationScorecard:
    intended = build_intended_outcome_report()
    realization = build_effect_realization_report()
    truth = build_post_action_truth_report()
    transitions = build_outcome_transition_report()

    not_computable = any(v == "OUTCOME_UNKNOWN" for v in intended["intendedStates"].values()) or any(
        v == "NOT_COMPUTABLE" for v in realization["realizationStates"].values()
    )
    blocked = any(v in {"ABSENT_OUTCOME", "BLOCKED"} for v in truth["truthStates"].values()) or any(
        x["verification_state"] in {"EFFECT_ABSENT", "VERIFICATION_REQUIRED"} for x in transitions["transitions"]
    )
    contradiction = any(v == "CONTRADICTORY_OUTCOME" for v in truth["truthStates"].values()) or any(
        x["verification_state"] == "OUTCOME_CONTRADICTORY" for x in transitions["transitions"]
    )
    delayed = any(v == "DELAYED_OUTCOME" for v in truth["truthStates"].values()) or any(
        x["verification_state"] == "EFFECT_DELAYED" for x in transitions["transitions"]
    )
    partial = any(v == "PARTIAL_REALIZED_OUTCOME" for v in truth["truthStates"].values()) or any(
        x["verification_state"] == "EFFECT_PARTIAL" for x in transitions["transitions"]
    )

    dimensions = {
        "intended_outcome_clarity": "DEGRADED" if any(v == "OUTCOME_UNKNOWN" for v in intended["intendedStates"].values()) else "CLEAR",
        "realization_validity": "AT_RISK"
        if any(v in {"EFFECT_INFERRED", "EFFECT_ACKNOWLEDGED", "VERIFICATION_REQUIRED", "NOT_COMPUTABLE"} for v in realization["realizationStates"].values())
        else "DISCIPLINED",
        "completion_vs_effect_discipline": "AT_RISK" if partial or delayed or blocked else "DISCIPLINED",
        "contradiction_visibility": "ELEVATED" if contradiction else "LOW",
        "false_success_burden": "ELEVATED" if blocked or contradiction else "LOW",
        "operator_truth_clarity": "EXPLICIT",
    }
    blockers = sorted(k for k, v in dimensions.items() if v in {"DEGRADED", "AT_RISK", "ELEVATED"})
    blockers.extend(sorted(x["code"] for x in intended["governanceErrors"] if x["severity"] == "ERROR"))
    blockers.extend(sorted(x["code"] for x in realization["governanceErrors"] if x["severity"] == "ERROR"))
    blockers.extend(sorted(x["code"] for x in truth["governanceErrors"] if x["severity"] == "ERROR"))
    blockers.extend(sorted(x["code"] for x in transitions["governanceErrors"] if x["severity"] == "ERROR"))
    blockers = sorted(set(blockers))

    evidence = {
        "intended": [intended["auditHash"]],
        "realization": [realization["auditHash"]],
        "truth": [truth["auditHash"]],
        "transitions": [transitions["auditHash"]],
    }
    category = _category(
        blocked=blocked,
        contradiction=contradiction,
        partial=partial,
        delayed=delayed,
        not_computable=not_computable,
    )
    payload = {"dimensions": dimensions, "evidence": evidence, "blockers": blockers, "category": category}
    return OutcomeVerificationScorecard(
        artifact_type="OutcomeVerificationScorecard.v1",
        artifact_id="outcome-verification-scorecard",
        dimensions=dimensions,
        evidence=evidence,
        blockers=blockers,
        category=category,
        scorecard_hash=sha256_bytes(dumps_stable(payload).encode("utf-8")),
    )
