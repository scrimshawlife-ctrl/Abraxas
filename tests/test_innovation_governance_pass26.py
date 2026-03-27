from __future__ import annotations

from abx.innovation.experimentClassification import (
    classify_experiment_surfaces,
    detect_experiment_taxonomy_drift,
    detect_hidden_experimental_influence,
)
from abx.innovation.experimentReports import build_experiment_audit_report
from abx.innovation.innovationScorecard import build_experimentation_governance_scorecard
from abx.innovation.lifecycleReports import build_innovation_lifecycle_audit_report
from abx.innovation.lifecycleTransitions import classify_lifecycle_states, detect_redundant_lifecycle_grammar
from abx.innovation.outcomeClassification import classify_outcome_comparability
from abx.innovation.portfolioClassification import classify_innovation_portfolio, detect_stale_experiment_drift
from abx.innovation.portfolioReports import build_innovation_portfolio_audit_report
from abx.innovation.promotionReadiness import build_promotion_readiness_records
from abx.innovation.researchReports import build_research_artifact_audit_report


def test_experimentation_surface_governance_determinism() -> None:
    assert classify_experiment_surfaces() == classify_experiment_surfaces()
    assert detect_experiment_taxonomy_drift() == []
    influence = detect_hidden_experimental_influence()
    assert influence == detect_hidden_experimental_influence()
    assert any(x["reason"] == "unbounded_influence" for x in influence)
    report = build_experiment_audit_report()
    assert report == build_experiment_audit_report()
    assert report["classification"]["production_prohibited"]


def test_research_hypothesis_discipline_determinism() -> None:
    assert classify_outcome_comparability() == classify_outcome_comparability()
    report_a = build_research_artifact_audit_report()
    report_b = build_research_artifact_audit_report()
    assert report_a == report_b
    assert report_a["comparability"]["promotable"]
    assert report_a["comparability"]["inconclusive"]


def test_lifecycle_promotion_clarity_determinism() -> None:
    assert classify_lifecycle_states() == classify_lifecycle_states()
    assert detect_redundant_lifecycle_grammar() == []
    readiness = build_promotion_readiness_records()
    assert readiness == build_promotion_readiness_records()
    assert any(x.readiness_state == "blocked" for x in readiness)
    report = build_innovation_lifecycle_audit_report()
    assert report == build_innovation_lifecycle_audit_report()
    assert report["states"]["promotion_ready"]


def test_portfolio_retirement_discipline_determinism() -> None:
    assert classify_innovation_portfolio() == classify_innovation_portfolio()
    stale = detect_stale_experiment_drift()
    assert stale == detect_stale_experiment_drift()
    assert stale
    report = build_innovation_portfolio_audit_report()
    assert report == build_innovation_portfolio_audit_report()
    assert report["retirement"]


def test_experimentation_governance_scorecard_determinism_and_blockers() -> None:
    a = build_experimentation_governance_scorecard()
    b = build_experimentation_governance_scorecard()
    assert a.__dict__ == b.__dict__
    assert "experimentation_surface_clarity" in a.blockers
    assert "promotion_readiness_visibility" in a.blockers
    assert "stale_experiment_burden" in a.blockers
