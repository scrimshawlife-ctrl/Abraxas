from __future__ import annotations

from abx.tradeoff.priorityClassification import classify_priority
from abx.tradeoff.priorityReports import build_priority_assignment_report
from abx.tradeoff.sacrificeClassification import classify_tradeoff
from abx.tradeoff.tradeoffReports import build_tradeoff_legibility_report
from abx.tradeoff.tradeoffScorecard import build_tradeoff_governance_scorecard
from abx.tradeoff.tradeoffScorecardSerialization import serialize_tradeoff_scorecard
from abx.tradeoff.transitionReports import build_weighting_transition_report
from abx.tradeoff.weightingClassification import classify_weighting
from abx.tradeoff.weightingReports import build_value_weighting_report


def test_value_weighting_determinism_and_classes() -> None:
    report_a = build_value_weighting_report()
    report_b = build_value_weighting_report()
    assert report_a == report_b
    assert set(report_a["weightingStates"].values()).issubset(
        {
            "CANON_WEIGHTING_ACTIVE",
            "LOCAL_WEIGHTING_ACTIVE",
            "TEMPORARY_WEIGHTING_ACTIVE",
            "EMERGENCY_WEIGHTING_ACTIVE",
            "HIDDEN_WEIGHTING_SUSPECTED",
            "VALUE_CONFLICT_UNRESOLVED",
            "BLOCKED",
            "NOT_COMPUTABLE",
        }
    )
    assert classify_weighting(weighting_state="CANON_WEIGHTING_ACTIVE", weighting_source="policy/canon") == "CANON_WEIGHTING_ACTIVE"


def test_priority_assignment_determinism_and_classes() -> None:
    report_a = build_priority_assignment_report()
    report_b = build_priority_assignment_report()
    assert report_a == report_b
    assert set(report_a["priorityStates"].values()).issuperset(
        {"CANON_PRIORITY", "SITUATIONAL_PRIORITY", "EMERGENCY_PRIORITY_OVERRIDE", "TEMPORARY_PRIORITY_OVERRIDE", "TIE_BREAK_PRIORITY", "PRIORITY_UNKNOWN"}
    )
    assert classify_priority(priority_state="UNKNOWN", tie_breaker="policy_order") == "CANON_PRIORITY"


def test_tradeoff_legibility_determinism_and_distinctions() -> None:
    report_a = build_tradeoff_legibility_report()
    report_b = build_tradeoff_legibility_report()
    assert report_a == report_b
    assert set(report_a["tradeoffStates"].values()).issuperset(
        {"TRADEOFF_LEGIBLE", "SACRIFICE_ACKNOWLEDGED", "COMPROMISE_SELECTED", "DOMINATION_SELECTED", "TRADEOFF_HIDDEN"}
    )
    assert (
        classify_tradeoff(
            tradeoff_state="TRADEOFF_LEGIBLE",
            sacrifice_state="HIDDEN_SACRIFICE_RISK",
            resolution_state="COMPROMISE_SELECTED",
        )
        == "TRADEOFF_HIDDEN"
    )


def test_weighting_transition_determinism() -> None:
    report_a = build_weighting_transition_report()
    report_b = build_weighting_transition_report()
    assert report_a == report_b
    assert {x["to_state"] for x in report_a["transitions"]}.issuperset(
        {
            "LOCAL_OPTIMIZATION_ACTIVE",
            "HIDDEN_WEIGHTING_ACTIVE",
            "STICKY_OVERRIDE_DETECTED",
            "CANON_PRIORITY_RESTORED",
            "VALUE_DRIFT_DETECTED",
        }
    )


def test_tradeoff_scorecard_determinism_and_blockers() -> None:
    score_a = build_tradeoff_governance_scorecard()
    score_b = build_tradeoff_governance_scorecard()
    assert score_a == score_b
    assert score_a.category in {
        "TRADEOFF_GOVERNED",
        "HIDDEN_WEIGHT_BURDENED",
        "OVERRIDE_BURDENED",
        "PARTIAL",
        "BLOCKED",
        "NOT_COMPUTABLE",
    }
    assert "weighting_clarity" in score_a.blockers
    assert serialize_tradeoff_scorecard(score_a) == serialize_tradeoff_scorecard(score_b)


def test_elegance_regression_guards() -> None:
    weighting = build_value_weighting_report()
    priority = build_priority_assignment_report()
    tradeoff = build_tradeoff_legibility_report()

    assert len(set(weighting["weightingStates"].values())) <= 5
    assert len(set(priority["priorityStates"].values())) <= 6
    assert any(x["tradeoff_state"] == "TRADEOFF_HIDDEN" for x in tradeoff["tradeoff"])
    assert any(x["code"] == "TRADEOFF_LEGIBILITY_FAIL" for x in tradeoff["governanceErrors"])
