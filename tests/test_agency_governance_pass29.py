from __future__ import annotations

from abx.agency.actionBoundaryReports import build_action_boundary_report
from abx.agency.actionModes import build_action_modes
from abx.agency.agencyScorecard import build_agency_governance_scorecard
from abx.agency.autonomousClassification import ACTION_MODE_CLASSES, classify_autonomous_posture
from abx.agency.autonomousReports import build_autonomous_operation_report
from abx.agency.delegationReports import build_delegation_report
from abx.agency.delegationRecords import build_delegation_chains
from abx.agency.guardrailReports import build_guardrail_report
from abx.agency.hiddenChannelDetection import build_hidden_channel_records


def test_autonomous_operation_classification_and_report_determinism() -> None:
    modes = build_action_modes()
    assert modes == build_action_modes()
    assert ACTION_MODE_CLASSES == {x.mode_class for x in modes}

    report_a = build_autonomous_operation_report()
    report_b = build_autonomous_operation_report()
    assert report_a == report_b
    assert classify_autonomous_posture(report_a["modeStates"]) == report_a["autonomousPosture"]


def test_delegation_chain_integrity_and_classification_determinism() -> None:
    chains_a = build_delegation_chains()
    chains_b = build_delegation_chains()
    assert chains_a == chains_b
    assert all(x.depth <= 2 for x in chains_a)

    report_a = build_delegation_report()
    report_b = build_delegation_report()
    assert report_a == report_b
    assert set(report_a["chainStates"].values()).issubset(
        {"DIRECT_EXECUTION", "ASSISTED_HANDOFF", "BOUNDED_DELEGATION", "ESCALATION", "RETRY_REDELIVERY", "RECURSIVE_DELEGATION_BLOCKED", "NOT_COMPUTABLE"}
    )


def test_guardrail_policy_trigger_and_posture_determinism() -> None:
    report_a = build_guardrail_report()
    report_b = build_guardrail_report()
    assert report_a == report_b
    assert report_a["guardrailPosture"] in {"GUARDRAILED", "DEGRADED", "BLOCKED", "PARTIAL", "NOT_COMPUTABLE"}
    assert all(t["trigger_state"] in {"TRIPPED", "NO_TRIP"} for t in report_a["triggers"])


def test_action_boundary_side_effect_and_hidden_channel_determinism() -> None:
    hidden_a = build_hidden_channel_records()
    hidden_b = build_hidden_channel_records()
    assert hidden_a == hidden_b

    report_a = build_action_boundary_report()
    report_b = build_action_boundary_report()
    assert report_a == report_b
    assert set(report_a["classification"]).issuperset(
        {"no_side_effects", "side_effect_observed", "side_effect_blocked", "hidden_channel_suspected", "hidden_channel_confirmed"}
    )


def test_agency_scorecard_determinism_blockers_and_category_logic() -> None:
    score_a = build_agency_governance_scorecard()
    score_b = build_agency_governance_scorecard()
    assert score_a == score_b
    assert score_a.category in {"ANALYSIS_ONLY", "BOUNDED_ACTION_READY", "PARTIAL", "BLOCKED", "HIDDEN_CHANNEL_RISK"}
    assert "hidden_channel_burden" in score_a.dimensions


def test_elegance_regression_and_invariance_guards() -> None:
    autonomous = build_autonomous_operation_report()
    delegation = build_delegation_report()
    boundary = build_action_boundary_report()

    # Duplicate agency vocabulary detection.
    assert set(autonomous["modeStates"].values()).issubset(
        {
            "ANALYSIS_ONLY",
            "RECOMMENDATION_ONLY",
            "OPERATOR_CONFIRMED_ACTION",
            "DELEGATED_ACTION",
            "BOUNDED_AUTONOMOUS_ACTION",
            "BLOCKED",
            "DEGRADED",
            "NOT_COMPUTABLE",
        }
    )

    # Redundant delegation grammar detection.
    assert set(delegation["chainStates"].values()).issubset(
        {"DIRECT_EXECUTION", "ASSISTED_HANDOFF", "BOUNDED_DELEGATION", "ESCALATION", "RETRY_REDELIVERY", "RECURSIVE_DELEGATION_BLOCKED", "NOT_COMPUTABLE"}
    )

    # Hidden authority expansion drift detection.
    assert all(len(row["hops"]) <= 2 for row in delegation["chains"])

    # Hidden-channel masking detection.
    if boundary["classification"]["hidden_channel_suspected"]:
        assert any("SUSPECTED" in row.risk_class for row in build_hidden_channel_records())
