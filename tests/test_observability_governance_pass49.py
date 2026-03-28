from __future__ import annotations

from abx.observability.blindSpotClassification import classify_blind_spot
from abx.observability.blindSpotReports import build_blind_spot_report
from abx.observability.coverageClassification import classify_coverage
from abx.observability.coverageReports import build_observability_coverage_report
from abx.observability.observabilityScorecard import build_observability_governance_scorecard
from abx.observability.observabilityScorecardSerialization import serialize_observability_scorecard
from abx.observability.sufficiencyClassification import classify_sufficiency
from abx.observability.sufficiencyReports import build_measurement_sufficiency_report
from abx.observability.transitionReports import build_observability_transition_report


def test_coverage_determinism_and_states() -> None:
    report_a = build_observability_coverage_report()
    report_b = build_observability_coverage_report()
    assert report_a == report_b
    assert set(report_a["coverageStates"].values()).issuperset(
        {
            "COVERAGE_SUFFICIENT",
            "COVERAGE_PARTIAL",
            "COVERAGE_DEGRADED",
            "NO_MEANINGFUL_COVERAGE",
            "COVERAGE_UNKNOWN",
            "NOT_COMPUTABLE",
        }
    )
    assert classify_coverage(coverage_state="COVERAGE_PARTIAL") == "COVERAGE_PARTIAL"


def test_blind_spot_determinism_and_states() -> None:
    report_a = build_blind_spot_report()
    report_b = build_blind_spot_report()
    assert report_a == report_b
    assert set(report_a["blindSpotStates"].values()).issuperset(
        {
            "BLIND_SPOT_SUSPECTED",
            "BLIND_SPOT_CONFIRMED",
            "BLIND_SPOT_TOLERABLE",
            "BLIND_SPOT_HIGH_RISK",
            "BLIND_SPOT_BLOCKED",
            "NOT_COMPUTABLE",
        }
    )
    assert classify_blind_spot(blind_spot_state="BLIND_SPOT_CONFIRMED") == "BLIND_SPOT_CONFIRMED"


def test_sufficiency_determinism_and_states() -> None:
    report_a = build_measurement_sufficiency_report()
    report_b = build_measurement_sufficiency_report()
    assert report_a == report_b
    assert set(report_a["sufficiencyStates"].values()).issuperset(
        {
            "SUFFICIENT_MEASUREMENT",
            "PROVISIONALLY_SUFFICIENT",
            "INSUFFICIENT_MEASUREMENT",
            "MEASUREMENT_AMBIGUOUS",
            "HIGH_CONSEQUENCE_UNDER_OBSERVED",
            "LOW_CONSEQUENCE_TOLERABLE_UNDER_MEASUREMENT",
            "NOT_COMPUTABLE",
        }
    )
    assert (
        classify_sufficiency(sufficiency_state="INSUFFICIENT_MEASUREMENT", consequence_class="HIGH_CONSEQUENCE")
        == "HIGH_CONSEQUENCE_UNDER_OBSERVED"
    )


def test_transition_determinism_and_states() -> None:
    report_a = build_observability_transition_report()
    report_b = build_observability_transition_report()
    assert report_a == report_b
    assert {x["to_state"] for x in report_a["transitions"]}.issuperset(
        {
            "PARTIAL_VISIBILITY_ACTIVE",
            "INSTRUMENTATION_STALE",
            "FALSE_ASSURANCE_RISK",
            "TRUST_RESTORED",
            "BLOCKED",
        }
    )


def test_observability_scorecard_determinism_and_blockers() -> None:
    score_a = build_observability_governance_scorecard()
    score_b = build_observability_governance_scorecard()
    assert score_a == score_b
    assert score_a.category in {
        "OBSERVABILITY_GOVERNED",
        "BLIND_SPOT_BURDENED",
        "INSUFFICIENT_MEASUREMENT_BURDENED",
        "STALE_INSTRUMENTATION_BURDENED",
        "PARTIAL",
        "BLOCKED",
        "NOT_COMPUTABLE",
    }
    assert "sufficiency_legitimacy" in score_a.blockers
    assert serialize_observability_scorecard(score_a) == serialize_observability_scorecard(score_b)


def test_elegance_regression_guards() -> None:
    coverage = build_observability_coverage_report()
    blind = build_blind_spot_report()
    sufficiency = build_measurement_sufficiency_report()

    assert len(set(coverage["coverageStates"].values())) <= 6
    assert len(set(blind["blindSpotStates"].values())) <= 6
    assert len(set(sufficiency["sufficiencyStates"].values())) <= 7
    assert any(x["code"] == "BLIND_SPOT_BLOCKING" for x in blind["governanceErrors"])
