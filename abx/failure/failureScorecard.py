from __future__ import annotations

from abx.failure.errorReports import build_error_taxonomy_report
from abx.failure.failureReports import build_failure_semantics_report
from abx.failure.recoveryReports import build_recovery_eligibility_report
from abx.failure.transitionReports import build_failure_transition_report
from abx.failure.types import FailureGovernanceScorecard
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def _category(*, blocked: bool, unsafe: bool, repeat_burden: bool, partial: bool) -> str:
    if blocked:
        return "BLOCKED"
    if unsafe:
        return "UNSAFE_RESTORATION_BURDENED"
    if repeat_burden:
        return "REPEAT_FAILURE_BURDENED"
    if partial:
        return "PARTIAL"
    return "FAILURE_GOVERNED"


def build_failure_governance_scorecard() -> FailureGovernanceScorecard:
    errors = build_error_taxonomy_report()
    failure = build_failure_semantics_report()
    recovery = build_recovery_eligibility_report()
    transitions = build_failure_transition_report()

    blocked = any(v in {"BLOCKED", "RECOVERY_FORBIDDEN"} for v in recovery["recoveryStates"].values())
    unsafe = bool(transitions["unsafeRestoration"])
    repeat_burden = any(x["from_state"] == "RETRY_ALLOWED" and x["to_state"] == "RETRY_FORBIDDEN" for x in transitions["transitions"])
    partial = any(v == "PARTIAL" for v in recovery["recoveryStates"].values())

    dimensions = {
        "error_taxonomy_clarity": "EXPLICIT",
        "recoverability_classification_quality": "VISIBLE",
        "retry_discipline_quality": "ELEVATED" if repeat_burden else "DISCIPLINED",
        "rollback_quarantine_rebuild_visibility": "VISIBLE",
        "integrity_risk_visibility": "VISIBLE" if transitions["integrityRisk"] else "PARTIAL",
        "degraded_vs_recovered_clarity": "EXPLICIT",
        "repeat_failure_burden": "ELEVATED" if repeat_burden else "LOW",
        "unsafe_restoration_burden": "ELEVATED" if unsafe else "LOW",
        "recovery_clearance_discipline": "BLOCKED" if blocked else "DISCIPLINED",
        "operator_failure_posture_clarity": "EXPLICIT",
    }
    blockers = sorted(k for k, v in dimensions.items() if v in {"ELEVATED", "BLOCKED", "NOT_COMPUTABLE"})
    evidence = {
        "errors": [errors["auditHash"]],
        "failure": [failure["auditHash"]],
        "recovery": [recovery["auditHash"]],
        "transitions": [transitions["auditHash"]],
    }
    category = _category(blocked=blocked, unsafe=unsafe, repeat_burden=repeat_burden, partial=partial)
    scorecard_hash = sha256_bytes(dumps_stable({"dimensions": dimensions, "evidence": evidence, "blockers": blockers, "category": category}).encode("utf-8"))
    return FailureGovernanceScorecard(
        artifact_type="FailureGovernanceScorecard.v1",
        artifact_id="failure-governance-scorecard",
        dimensions=dimensions,
        evidence=evidence,
        blockers=blockers,
        category=category,
        scorecard_hash=scorecard_hash,
    )
