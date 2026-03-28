from __future__ import annotations

from abx.outcome.effectRealizationClassification import classify_effect_realization
from abx.outcome.effectRealizationReports import build_effect_realization_report
from abx.outcome.intendedOutcomeClassification import classify_intended_outcome
from abx.outcome.intendedOutcomeReports import build_intended_outcome_report
from abx.outcome.outcomeScorecard import build_outcome_verification_scorecard
from abx.outcome.outcomeScorecardSerialization import serialize_outcome_scorecard
from abx.outcome.outcomeTransitionReports import build_outcome_transition_report
from abx.outcome.postActionTruthClassification import classify_post_action_truth
from abx.outcome.postActionTruthReports import build_post_action_truth_report


def test_intended_outcome_determinism_and_states() -> None:
    report_a = build_intended_outcome_report()
    report_b = build_intended_outcome_report()
    assert report_a == report_b
    assert set(report_a["intendedStates"].values()).issuperset(
        {"INTENDED_EFFECT", "SIDE_EFFECT", "DOWNSTREAM_EFFECT", "NO_EFFECT_EXPECTED", "OUTCOME_UNKNOWN"}
    )
    assert classify_intended_outcome(intended_state="INTENDED_EFFECT") == "INTENDED_EFFECT"


def test_effect_realization_determinism_and_states() -> None:
    report_a = build_effect_realization_report()
    report_b = build_effect_realization_report()
    assert report_a == report_b
    assert set(report_a["realizationStates"].values()).issuperset(
        {"EFFECT_OBSERVED", "EFFECT_ACKNOWLEDGED", "EFFECT_INFERRED", "VERIFICATION_REQUIRED", "NOT_COMPUTABLE"}
    )
    assert classify_effect_realization(realization_state="EFFECT_UNVERIFIED", evidence_mode="ASSUMED") == "VERIFICATION_REQUIRED"


def test_post_action_truth_determinism_and_states() -> None:
    report_a = build_post_action_truth_report()
    report_b = build_post_action_truth_report()
    assert report_a == report_b
    assert set(report_a["truthStates"].values()).issuperset(
        {
            "FULL_REALIZED_OUTCOME",
            "PARTIAL_REALIZED_OUTCOME",
            "DELAYED_OUTCOME",
            "ABSENT_OUTCOME",
            "CONTRADICTORY_OUTCOME",
            "BLOCKED",
        }
    )
    assert classify_post_action_truth(truth_state="FULL_REALIZED_OUTCOME") == "FULL_REALIZED_OUTCOME"


def test_outcome_transition_determinism_and_classes() -> None:
    report_a = build_outcome_transition_report()
    report_b = build_outcome_transition_report()
    assert report_a == report_b
    assert {x["verification_state"] for x in report_a["transitions"]}.issuperset(
        {
            "ACTION_COMPLETED",
            "EFFECT_OBSERVED",
            "EFFECT_ACKNOWLEDGED",
            "EFFECT_PARTIAL",
            "EFFECT_DELAYED",
            "EFFECT_ABSENT",
            "OUTCOME_CONTRADICTORY",
            "VERIFICATION_REQUIRED",
        }
    )


def test_outcome_scorecard_determinism_and_blockers() -> None:
    score_a = build_outcome_verification_scorecard()
    score_b = build_outcome_verification_scorecard()
    assert score_a == score_b
    assert score_a.category in {
        "OUTCOME_VERIFIED",
        "DELAYED_BURDENED",
        "CONTRADICTORY_BURDENED",
        "PARTIAL",
        "BLOCKED",
        "NOT_COMPUTABLE",
    }
    assert "false_success_burden" in score_a.blockers
    assert serialize_outcome_scorecard(score_a) == serialize_outcome_scorecard(score_b)


def test_elegance_regression_guards() -> None:
    intended = build_intended_outcome_report()
    realization = build_effect_realization_report()
    truth = build_post_action_truth_report()

    assert len(set(intended["intendedStates"].values())) <= 5
    assert len(set(realization["realizationStates"].values())) <= 5
    assert len(set(truth["truthStates"].values())) <= 6
    assert any(x["code"] == "POST_ACTION_TRUTH_BLOCKING" for x in truth["governanceErrors"])
