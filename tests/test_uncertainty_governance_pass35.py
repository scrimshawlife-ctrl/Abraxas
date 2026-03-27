from __future__ import annotations

from abx.uncertainty.calibrationClassification import classify_calibration
from abx.uncertainty.calibrationReports import build_calibration_report
from abx.uncertainty.confidenceExpressionClassification import classify_confidence_expression
from abx.uncertainty.confidenceExpressionReports import build_confidence_expression_report
from abx.uncertainty.transitionReports import build_confidence_transition_report
from abx.uncertainty.uncertaintyClassification import classify_uncertainty
from abx.uncertainty.uncertaintyReports import build_uncertainty_report
from abx.uncertainty.uncertaintyScorecard import build_uncertainty_governance_scorecard


def test_uncertainty_representation_determinism() -> None:
    report_a = build_uncertainty_report()
    report_b = build_uncertainty_report()
    assert report_a == report_b
    assert set(report_a["uncertaintyStates"].values()).issubset(
        {"UNCERTAINTY_LOW", "UNCERTAINTY_MODERATE", "UNCERTAINTY_HIGH", "UNCERTAINTY_MIXED", "OUTPUT_DOWNGRADE_REQUIRED", "NOT_COMPUTABLE"}
    )
    assert classify_uncertainty(uncertainty_level="HIGH", downgrade_required="YES") == "OUTPUT_DOWNGRADE_REQUIRED"


def test_confidence_expression_semantics_determinism() -> None:
    report_a = build_confidence_expression_report()
    report_b = build_confidence_expression_report()
    assert report_a == report_b
    assert set(report_a["expressionStates"].values()).issubset(
        {"NUMERIC", "CATEGORICAL", "INTERVAL", "QUALITATIVE", "SUPPRESSED", "ABSTAIN_FROM_CONFIDENCE", "NOT_COMPUTABLE"}
    )
    assert classify_confidence_expression("INTERVAL") == "INTERVAL"


def test_calibration_validity_determinism() -> None:
    report_a = build_calibration_report()
    report_b = build_calibration_report()
    assert report_a == report_b
    assert set(report_a["calibrationStates"].values()).issubset(
        {
            "CALIBRATED",
            "PROVISIONALLY_CALIBRATED",
            "PARTIALLY_CALIBRATED",
            "STALE_CALIBRATION",
            "UNCALIBRATED",
            "RECALIBRATION_REQUIRED",
            "BLOCKED_FOR_INVALID_CALIBRATION",
            "NOT_COMPUTABLE",
        }
    )
    assert classify_calibration("CALIBRATED") == "CALIBRATED"


def test_confidence_transition_determinism() -> None:
    report_a = build_confidence_transition_report()
    report_b = build_confidence_transition_report()
    assert report_a == report_b
    assert {x["to_state"] for x in report_a["transitions"]}.issuperset(
        {"SUPPRESSED", "QUALITATIVE", "ABSTAIN_FROM_CONFIDENCE", "NUMERIC"}
    )


def test_uncertainty_scorecard_determinism_and_blockers() -> None:
    score_a = build_uncertainty_governance_scorecard()
    score_b = build_uncertainty_governance_scorecard()
    assert score_a == score_b
    assert score_a.category in {"UNCERTAINTY_GOVERNED", "PSEUDO_PRECISION_BURDENED", "STALE_CALIBRATION_BURDENED", "PARTIAL", "BLOCKED"}
    assert "calibration_validity_quality" in score_a.dimensions


def test_elegance_regressions_and_invariance_guards() -> None:
    uncertainty = build_uncertainty_report()
    expression = build_confidence_expression_report()
    calibration = build_calibration_report()
    transitions = build_confidence_transition_report()

    assert len(set(uncertainty["uncertaintyStates"].values())) <= 6
    assert len(set(expression["expressionStates"].values())) <= 7
    if any(v in {"UNCALIBRATED", "RECALIBRATION_REQUIRED"} for v in calibration["calibrationStates"].values()):
        assert any(x["to_state"] in {"SUPPRESSED", "ABSTAIN_FROM_CONFIDENCE"} for x in transitions["transitions"])
