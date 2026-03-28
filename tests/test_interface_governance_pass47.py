from __future__ import annotations

from abx.interface.acceptanceReports import build_receiver_acceptance_report
from abx.interface.contractClassification import classify_contract
from abx.interface.contractReports import build_interface_contract_report
from abx.interface.deliveryClassification import classify_handoff
from abx.interface.handoffReports import build_handoff_reliability_report
from abx.interface.interfaceScorecard import build_cross_boundary_delivery_scorecard
from abx.interface.interfaceScorecardSerialization import serialize_interface_scorecard
from abx.interface.interpretationClassification import classify_acceptance
from abx.interface.transitionReports import build_interface_transition_report


def test_contract_determinism_and_states() -> None:
    report_a = build_interface_contract_report()
    report_b = build_interface_contract_report()
    assert report_a == report_b
    assert set(report_a["contractStates"].values()).issuperset(
        {
            "STRUCTURAL_VALID",
            "SEMANTIC_VALID",
            "IDENTITY_PRESERVING",
            "FRESHNESS_VALID",
            "AUTHORITY_VALID",
            "CONTRACT_DRIFT_SUSPECTED",
            "CONTRACT_BROKEN",
            "NOT_COMPUTABLE",
        }
    )
    assert classify_contract(contract_state="CONTRACT_VALID", integrity_surface="SEMANTIC_VALID") == "SEMANTIC_VALID"


def test_handoff_determinism_and_states() -> None:
    report_a = build_handoff_reliability_report()
    report_b = build_handoff_reliability_report()
    assert report_a == report_b
    assert set(report_a["handoffStates"].values()).issuperset(
        {
            "HANDOFF_PREPARED",
            "HANDOFF_SENT",
            "HANDOFF_DELIVERED",
            "HANDOFF_RECEIVED",
            "HANDOFF_PENDING",
            "HANDOFF_FAILED",
            "HANDOFF_UNKNOWN",
            "NOT_COMPUTABLE",
        }
    )
    assert classify_handoff(handoff_state="HANDOFF_SENT") == "HANDOFF_SENT"


def test_receiver_acceptance_determinism_and_states() -> None:
    report_a = build_receiver_acceptance_report()
    report_b = build_receiver_acceptance_report()
    assert report_a == report_b
    assert set(report_a["acceptanceStates"].values()).issuperset(
        {
            "RECEIVED_UNACCEPTED",
            "ACCEPTED_STRUCTURAL",
            "ACCEPTED_SEMANTIC",
            "ACCEPTED_APPLIED",
            "REJECTED",
            "COERCED_DEFAULTED",
            "INTERPRETATION_MISMATCH",
            "NOT_COMPUTABLE",
        }
    )
    assert (
        classify_acceptance(acceptance_state="REJECTED", interpretation_state="INTERPRETATION_REJECTED") == "REJECTED"
    )


def test_interface_transition_determinism_and_states() -> None:
    report_a = build_interface_transition_report()
    report_b = build_interface_transition_report()
    assert report_a == report_b
    assert {x["to_state"] for x in report_a["transitions"]}.issuperset(
        {
            "HANDOFF_SENT",
            "HANDOFF_DELIVERED",
            "HANDOFF_RECEIVED",
            "HANDOFF_ACCEPTED",
            "DELIVERY_PARTIAL",
            "HANDOFF_REJECTED",
            "DELIVERY_DUPLICATED",
            "NOT_COMPUTABLE",
        }
    )


def test_interface_scorecard_determinism_and_blockers() -> None:
    score_a = build_cross_boundary_delivery_scorecard()
    score_b = build_cross_boundary_delivery_scorecard()
    assert score_a == score_b
    assert score_a.category in {
        "CROSS_BOUNDARY_GOVERNED",
        "DEGRADED_HANDOFF_BURDENED",
        "MISMATCH_BURDENED",
        "PARTIAL",
        "BLOCKED",
        "NOT_COMPUTABLE",
    }
    assert "delivery_integrity" in score_a.blockers
    assert serialize_interface_scorecard(score_a) == serialize_interface_scorecard(score_b)


def test_elegance_regression_guards() -> None:
    contract = build_interface_contract_report()
    handoff = build_handoff_reliability_report()
    acceptance = build_receiver_acceptance_report()

    assert len(set(contract["contractStates"].values())) <= 8
    assert len(set(handoff["handoffStates"].values())) <= 8
    assert len(set(acceptance["acceptanceStates"].values())) <= 8
    assert any(x["code"] == "HANDOFF_BLOCKING" for x in handoff["governanceErrors"])
