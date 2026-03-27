from __future__ import annotations

from abx.evidence.evidenceScorecard import build_evidence_governance_scorecard
from abx.evidence.readinessClassification import classify_readiness
from abx.evidence.readinessReports import build_readiness_report
from abx.evidence.sufficiencyClassification import classify_sufficiency
from abx.evidence.sufficiencyReports import build_sufficiency_report
from abx.evidence.thresholdClassification import classify_threshold_state
from abx.evidence.thresholdReports import build_threshold_report
from abx.evidence.transitionReports import build_evidence_transition_report


def test_threshold_governance_and_determinism() -> None:
    report_a = build_threshold_report()
    report_b = build_threshold_report()
    assert report_a == report_b
    assert set(report_a["thresholdStates"].values()).issubset(
        {"THRESHOLD_MET", "THRESHOLD_PROVISIONALLY_MET", "THRESHOLD_UNMET", "ESCALATION_REQUIRED", "NOT_COMPUTABLE"}
    )
    assert classify_threshold_state(threshold_value=0.8, evidence_strength=0.82, consequence_level="HIGH") == "THRESHOLD_MET"


def test_burden_sufficiency_semantics_and_determinism() -> None:
    report_a = build_sufficiency_report()
    report_b = build_sufficiency_report()
    assert report_a == report_b
    assert set(x["sufficiency_state"] for x in report_a["sufficiency"]).issubset(
        {"BURDEN_MET", "BURDEN_PROVISIONALLY_MET", "BURDEN_UNMET", "CONFLICTING_EVIDENCE", "ESCALATION_REQUIRED", "NOT_COMPUTABLE"}
    )
    assert classify_sufficiency(threshold_state="THRESHOLD_PROVISIONALLY_MET", conflict_state="NO_CONFLICT") == "BURDEN_PROVISIONALLY_MET"


def test_decision_readiness_semantics_and_determinism() -> None:
    report_a = build_readiness_report()
    report_b = build_readiness_report()
    assert report_a == report_b
    assert set(x["readiness_state"] for x in report_a["readiness"]).issubset(
        {"READY_TO_DECIDE", "READY_PROVISIONALLY", "DEFERRED_PENDING_EVIDENCE", "ABSTAINED", "ESCALATED", "BLOCKED", "NOT_COMPUTABLE"}
    )
    assert classify_readiness(sufficiency_state="BURDEN_UNMET", consequence_level="HIGH") == "ESCALATED"


def test_evidence_transition_determinism() -> None:
    report_a = build_evidence_transition_report()
    report_b = build_evidence_transition_report()
    assert report_a == report_b
    assert {x["to_state"] for x in report_a["transitions"]}.issuperset(
        {"BURDEN_PROVISIONALLY_MET", "BURDEN_UNMET", "CONFLICTING_EVIDENCE", "BURDEN_MET", "READY_TO_DECIDE"}
    )


def test_evidence_scorecard_determinism_and_blockers() -> None:
    score_a = build_evidence_governance_scorecard()
    score_b = build_evidence_governance_scorecard()
    assert score_a == score_b
    assert score_a.category in {"SUFFICIENCY_READY", "PROVISIONAL_BURDENED", "CONFLICT_BURDENED", "PARTIAL", "BLOCKED"}
    assert "threshold_state_clarity" in score_a.dimensions


def test_elegance_regressions_and_invariance_guards() -> None:
    threshold = build_threshold_report()
    sufficiency = build_sufficiency_report()
    readiness = build_readiness_report()
    transitions = build_evidence_transition_report()

    assert len(set(threshold["thresholdStates"].values())) <= 5
    assert len(set(x["sufficiency_state"] for x in sufficiency["sufficiency"])) <= 6
    assert not any(x["readiness_state"] == "READY_TO_DECIDE" and x["decision_class"] == "POLICY_EXCEPTION" for x in readiness["readiness"])
    if any(x["provisional_state"] == "PROVISIONAL_DECISION_EXPIRED" for x in transitions["provisional"]):
        assert any(x["to_state"] in {"BURDEN_UNMET", "CONFLICTING_EVIDENCE"} for x in transitions["transitions"])
