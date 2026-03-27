from __future__ import annotations

from abx.human_factors.actionGrammar import detect_action_grammar_drift
from abx.human_factors.actionReports import build_warning_action_audit_report
from abx.human_factors.cognitiveReports import build_cognitive_load_audit_report
from abx.human_factors.humanFactorsScorecard import build_human_factors_scorecard
from abx.human_factors.interactionClassification import (
    classify_interaction_surfaces,
    detect_duplicate_interaction_surfaces,
)
from abx.human_factors.interactionReports import build_interaction_audit_report
from abx.human_factors.pathClassification import classify_operator_paths
from abx.human_factors.pathReports import build_operator_path_audit_report
from abx.human_factors.pathTransitions import build_path_transitions
from abx.human_factors.salienceClassification import classify_salience, classify_urgency
from abx.human_factors.summaryGrammar import detect_redundant_summary_surfaces
from abx.human_factors.warningGrammar import detect_inconsistent_warning_vocabulary


def test_interaction_surface_governance_stability() -> None:
    assert classify_interaction_surfaces() == classify_interaction_surfaces()
    assert detect_duplicate_interaction_surfaces() == []
    report = build_interaction_audit_report()
    assert report == build_interaction_audit_report()
    assert report["classification"]["primary"]


def test_cognitive_load_and_prioritization_stability() -> None:
    assert classify_salience() == classify_salience()
    assert classify_urgency() == classify_urgency()
    report = build_cognitive_load_audit_report()
    assert report == build_cognitive_load_audit_report()
    assert report["salienceClassification"]["must_act_now"]


def test_warning_summary_action_grammar_stability() -> None:
    assert detect_inconsistent_warning_vocabulary() == []
    assert detect_redundant_summary_surfaces() == ["summary.legacy.dashboard"]
    assert detect_action_grammar_drift() == []
    report = build_warning_action_audit_report()
    assert report == build_warning_action_audit_report()


def test_operator_path_clarity_and_transition_stability() -> None:
    assert classify_operator_paths() == classify_operator_paths()
    assert build_path_transitions() == build_path_transitions()
    report = build_operator_path_audit_report()
    assert report == build_operator_path_audit_report()
    assert report["classification"]["canonical"]


def test_human_factors_scorecard_determinism_and_blockers() -> None:
    a = build_human_factors_scorecard()
    b = build_human_factors_scorecard()
    assert a.__dict__ == b.__dict__
    assert "redundancy_burden" in a.blockers
    assert "drilldown_layering_quality" in a.blockers
