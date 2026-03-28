from __future__ import annotations

from abx.freshness.decayClassification import classify_freshness
from abx.freshness.freshnessReports import build_freshness_decay_report
from abx.freshness.freshnessScorecard import build_freshness_governance_scorecard
from abx.freshness.freshnessScorecardSerialization import serialize_freshness_scorecard
from abx.freshness.horizonClassification import classify_horizon
from abx.freshness.horizonReports import build_time_horizon_report
from abx.freshness.stalenessReports import build_staleness_report
from abx.freshness.transitionReports import build_freshness_transition_report


def test_time_horizon_determinism_and_classes() -> None:
    report_a = build_time_horizon_report()
    report_b = build_time_horizon_report()
    assert report_a == report_b
    assert set(report_a["horizonStates"].values()).issuperset(
        {"REAL_TIME_HORIZON", "SHORT_HORIZON", "MEDIUM_HORIZON", "LONG_HORIZON", "ARCHIVAL_HORIZON", "HORIZON_UNKNOWN"}
    )
    assert classify_horizon(horizon_state="REAL_TIME_HORIZON", cadence_ref="cadence/5m") == "REAL_TIME_HORIZON"


def test_freshness_decay_determinism_and_reuse_states() -> None:
    report_a = build_freshness_decay_report()
    report_b = build_freshness_decay_report()
    assert report_a == report_b
    assert set(report_a["freshnessStates"].values()).issuperset(
        {"FRESH", "FRESH_WITH_WARNING", "AGING", "STALE", "EXPIRED", "ARCHIVAL_ONLY", "DECAY_UNKNOWN", "REUSE_BLOCKED"}
    )
    assert classify_freshness(freshness_state="EXPIRED", reuse_posture="REUSE_BLOCKED", decay_state="DECAY_THRESHOLD") == "EXPIRED"


def test_staleness_archival_determinism() -> None:
    report_a = build_staleness_report()
    report_b = build_staleness_report()
    assert report_a == report_b
    assert {x["staleness_state"] for x in report_a["staleness"]}.issuperset(
        {"OPERATIONALLY_VALID", "AGING_BUT_VALID", "STALE_BUT_VISIBLE", "EXPIRED_FOR_OPERATIONAL_USE", "ARCHIVAL_VALID_ONLY", "STALE_SUPPORT_ACTIVE"}
    )


def test_freshness_transition_determinism() -> None:
    report_a = build_freshness_transition_report()
    report_b = build_freshness_transition_report()
    assert report_a == report_b
    assert {x["to_state"] for x in report_a["transitions"]}.issuperset(
        {"REFRESH_REQUIRED", "STALE_SUPPORT_ACTIVE", "REFRESH_OVERDUE", "ARCHIVAL_DOWNGRADE_ACTIVE", "REUSE_BLOCKED", "FRESHNESS_RESTORED"}
    )


def test_freshness_scorecard_determinism_and_blockers() -> None:
    score_a = build_freshness_governance_scorecard()
    score_b = build_freshness_governance_scorecard()
    assert score_a == score_b
    assert score_a.category in {
        "FRESHNESS_GOVERNED",
        "AGE_RISK_BURDENED",
        "REFRESH_OVERDUE_BURDENED",
        "PARTIAL",
        "BLOCKED",
        "NOT_COMPUTABLE",
    }
    assert "freshness_classification_quality" in score_a.blockers
    assert serialize_freshness_scorecard(score_a) == serialize_freshness_scorecard(score_b)


def test_elegance_regression_guards() -> None:
    horizon = build_time_horizon_report()
    freshness = build_freshness_decay_report()
    staleness = build_staleness_report()

    assert len(set(horizon["horizonStates"].values())) <= 6
    assert len(set(freshness["freshnessStates"].values())) <= 8
    assert any(x["staleness_state"] == "STALE_SUPPORT_ACTIVE" for x in staleness["staleness"])
    assert any(x["code"] == "FRESHNESS_INVALID_FOR_REUSE" for x in freshness["governanceErrors"])
