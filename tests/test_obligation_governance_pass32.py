from __future__ import annotations

from abx.obligations.commitmentReports import build_external_commitment_report
from abx.obligations.dueStateClassification import classify_due_state
from abx.obligations.dueStateReports import build_due_state_report
from abx.obligations.obligationReports import build_obligation_lifecycle_report
from abx.obligations.obligationScorecard import build_obligation_governance_scorecard
from abx.obligations.transitionReports import build_obligation_transition_report


def test_external_commitment_classification_and_reporting_determinism() -> None:
    report_a = build_external_commitment_report()
    report_b = build_external_commitment_report()
    assert report_a == report_b
    assert set(report_a["commitmentStates"].values()).issubset(
        {
            "PROPOSED_COMMITMENT",
            "ACCEPTED_COMMITMENT",
            "CONDITIONAL_COMMITMENT",
            "SCHEDULED_OBLIGATION",
            "SUPERSEDED_OBLIGATION",
            "CANCELED_OBLIGATION",
            "BLOCKED",
            "DEGRADED",
            "NOT_COMPUTABLE",
        }
    )


def test_deadline_due_state_semantics_and_reporting_determinism() -> None:
    report_a = build_due_state_report()
    report_b = build_due_state_report()
    assert report_a == report_b
    assert all(x["due_state"] in {"SCHEDULED", "DUE_SOON", "AT_RISK", "SUPERSEDED", "NOT_COMPUTABLE"} for x in report_a["dueStates"])
    assert classify_due_state(deadline_kind="HARD_DEADLINE", commitment_state="ACCEPTED_COMMITMENT", due_date="2026-06-30") == ("DUE_SOON", "AT_RISK")


def test_obligation_lifecycle_discharge_linkage_determinism() -> None:
    report_a = build_obligation_lifecycle_report()
    report_b = build_obligation_lifecycle_report()
    assert report_a == report_b
    assert set(report_a["obligationStates"].values()).issubset(
        {"ACCEPTED", "SCHEDULED", "IN_PROGRESS", "DUE_SOON", "AT_RISK", "BLOCKED", "DISCHARGED", "PARTIALLY_DISCHARGED", "MISSED", "WAIVED", "NOT_COMPUTABLE"}
    )


def test_obligation_transition_reporting_determinism() -> None:
    report_a = build_obligation_transition_report()
    report_b = build_obligation_transition_report()
    assert report_a == report_b
    assert report_a["transitions"]
    assert set(x["to_state"] for x in report_a["transitions"]).issubset({"IN_PROGRESS", "DUE_SOON", "SCHEDULED", "MISSED", "WAIVED"})


def test_obligation_scorecard_determinism_and_blocker_logic() -> None:
    score_a = build_obligation_governance_scorecard()
    score_b = build_obligation_governance_scorecard()
    assert score_a == score_b
    assert score_a.category in {"COMMITMENT_READY", "RISK_LADEN", "MISS_BURDENED", "BLOCKED"}
    assert "risk_slip_miss_visibility" in score_a.dimensions


def test_elegance_regressions_and_invariance_guards() -> None:
    commitment = build_external_commitment_report()
    due = build_due_state_report()
    lifecycle = build_obligation_lifecycle_report()

    # Duplicate obligation vocabulary detection.
    assert len(set(commitment["commitmentStates"].values())) <= 9

    # Redundant due-state grammar detection.
    assert set(x["risk_state"] for x in due["dueStates"]).issubset({"AT_RISK", "LOW", "NOT_COMPUTABLE"})

    # Silent-slip masking detection.
    if any(x["due_state"] == "AT_RISK" for x in due["dueStates"]):
        assert any(x["to_state"] == "MISSED" for x in build_obligation_transition_report()["transitions"])

    # Commitment inflation drift detection.
    assert not (
        any(v == "PROPOSED_COMMITMENT" for v in commitment["commitmentStates"].values())
        and all(v == "DISCHARGED" for v in lifecycle["obligationStates"].values())
    )
