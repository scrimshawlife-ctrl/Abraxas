from __future__ import annotations

from abx.uncertainty.calibrationReports import build_calibration_report
from abx.uncertainty.confidenceExpressionReports import build_confidence_expression_report
from abx.uncertainty.transitionReports import build_confidence_transition_report
from abx.uncertainty.uncertaintyReports import build_uncertainty_report
from abx.uncertainty.types import UncertaintyGovernanceScorecard
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def _category(*, blocked: bool, pseudo_precision: bool, stale: bool, suppressed: bool) -> str:
    if blocked:
        return "BLOCKED"
    if pseudo_precision:
        return "PSEUDO_PRECISION_BURDENED"
    if stale:
        return "STALE_CALIBRATION_BURDENED"
    if suppressed:
        return "PARTIAL"
    return "UNCERTAINTY_GOVERNED"


def build_uncertainty_governance_scorecard() -> UncertaintyGovernanceScorecard:
    uncertainty = build_uncertainty_report()
    expression = build_confidence_expression_report()
    calibration = build_calibration_report()
    transitions = build_confidence_transition_report()

    suppressed = any(x["suppression_state"] in {"CONFIDENCE_SUPPRESSED", "ABSTAIN_FROM_CONFIDENCE"} for x in transitions["suppression"])
    blocked = any(v in {"UNCALIBRATED", "RECALIBRATION_REQUIRED", "BLOCKED_FOR_INVALID_CALIBRATION"} for v in calibration["calibrationStates"].values())
    pseudo_precision = any(v == "NUMERIC" for v in expression["expressionStates"].values()) and blocked
    stale = any(v in {"PROVISIONALLY_CALIBRATED", "PARTIALLY_CALIBRATED"} for v in calibration["calibrationStates"].values())

    dimensions = {
        "uncertainty_type_clarity": "EXPLICIT",
        "confidence_expression_discipline": "SUPPRESSED_VISIBLE" if suppressed else "DISCIPLINED",
        "calibration_validity_quality": "INVALID_PRESENT" if blocked else "VALID",
        "suppression_abstention_legibility": "VISIBLE",
        "stale_calibration_burden": "ELEVATED" if stale else "LOW",
        "miscalibration_visibility": "VISIBLE" if transitions["miscalibration"] else "PARTIAL",
        "pseudo_precision_burden": "ELEVATED" if pseudo_precision else "LOW",
        "provisional_calibration_hygiene": "ELEVATED" if stale else "LOW",
        "confidence_output_clarity": "BLOCKED" if blocked else "EXPLICIT",
        "operator_uncertainty_posture_clarity": "EXPLICIT",
    }
    blockers = sorted(k for k, v in dimensions.items() if v in {"INVALID_PRESENT", "ELEVATED", "BLOCKED", "NOT_COMPUTABLE"})
    evidence = {
        "uncertainty": [uncertainty["auditHash"]],
        "expression": [expression["auditHash"]],
        "calibration": [calibration["auditHash"]],
        "transitions": [transitions["auditHash"]],
    }
    category = _category(blocked=blocked, pseudo_precision=pseudo_precision, stale=stale, suppressed=suppressed)
    scorecard_hash = sha256_bytes(dumps_stable({"dimensions": dimensions, "evidence": evidence, "blockers": blockers, "category": category}).encode("utf-8"))
    return UncertaintyGovernanceScorecard(
        artifact_type="UncertaintyGovernanceScorecard.v1",
        artifact_id="uncertainty-governance-scorecard",
        dimensions=dimensions,
        evidence=evidence,
        blockers=blockers,
        category=category,
        scorecard_hash=scorecard_hash,
    )
