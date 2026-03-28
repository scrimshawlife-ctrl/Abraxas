from __future__ import annotations

from abx.operator.humanOverrideRecords import build_human_override_records
from abx.operator.interventionClassification import classify_intervention_kind, classify_intervention_legitimacy
from abx.operator.interventionReports import build_intervention_report
from abx.operator.manualInterventionRecords import build_manual_intervention_records
from abx.operator.operatorScorecard import build_operator_governance_scorecard
from abx.operator.operatorTraceRecords import build_operator_trace_records
from abx.operator.overrideClassification import classify_override_state
from abx.operator.overrideReports import build_override_report
from abx.operator.traceClassification import classify_reason_quality, classify_scope, classify_trace_completeness
from abx.operator.traceReports import build_traceability_report
from abx.operator.transitionReports import build_operator_transition_report


def test_override_states_and_deterministic_report() -> None:
    report_a = build_override_report()
    report_b = build_override_report()
    assert report_a == report_b
    assert set(report_a["overrideStates"].values()).issubset(
        {
            "OVERRIDE_REQUESTED",
            "OVERRIDE_APPROVED",
            "OVERRIDE_ACTIVE",
            "OVERRIDE_DENIED",
            "OVERRIDE_FORBIDDEN",
            "NOT_COMPUTABLE",
        }
    )
    record = next(x for x in build_human_override_records() if x.override_id == "ovr.emergency.feed-freeze.001")
    assert classify_override_state(record) == "OVERRIDE_ACTIVE"


def test_manual_intervention_type_legitimacy_and_determinism() -> None:
    report_a = build_intervention_report()
    report_b = build_intervention_report()
    assert report_a == report_b
    assert set(report_a["interventionKinds"].values()).issubset(
        {
            "CORRECTIVE_INTERVENTION",
            "EMERGENCY_INTERVENTION",
            "MAINTENANCE_INTERVENTION",
            "INVESTIGATORY_INTERVENTION",
            "BYPASS_INTERVENTION",
            "PROHIBITED_INTERVENTION",
            "INTERVENTION_UNKNOWN",
        }
    )
    records = build_manual_intervention_records()
    prohibited = next(x for x in records if x.intervention_id == "int.prohibited.policy-disable.001")
    assert classify_intervention_kind(prohibited) == "PROHIBITED_INTERVENTION"
    assert classify_intervention_legitimacy(prohibited) == "MANUAL_INTERVENTION_ILLEGITIMATE"


def test_traceability_scope_reversibility_and_determinism() -> None:
    report_a = build_traceability_report()
    report_b = build_traceability_report()
    assert report_a == report_b
    assert set(report_a["traceCompleteness"].values()).issubset({"TRACE_COMPLETE", "TRACE_PARTIAL"})
    assert set(report_a["reasonQuality"].values()).issubset({"REASON_EXPLICIT", "REASON_INSUFFICIENT"})
    assert {x["scope_state"] for x in report_a["scopeRecords"]}.issubset({"SCOPE_BOUNDED", "SCOPE_OVERBROAD"})
    trace = next(x for x in build_operator_trace_records() if x.trace_id == "trc.bypass.direct-write.001")
    assert classify_trace_completeness(trace) == "TRACE_PARTIAL"
    assert classify_reason_quality(trace) == "REASON_INSUFFICIENT"
    assert classify_scope(trace).scope_state == "SCOPE_OVERBROAD"


def test_operator_transitions_and_scorecard_determinism() -> None:
    transition_a = build_operator_transition_report()
    transition_b = build_operator_transition_report()
    assert transition_a == transition_b
    states = set(transition_a["transitionStates"].values())
    assert {
        "EMERGENCY_MANUAL_MODE_ACTIVE",
        "EMERGENCY_MODE_EXPIRED",
        "OVERRIDE_OVERBROAD_ACTIVE",
        "MANUAL_INTERVENTION_NOT_RESTORED",
    }.issubset(states)

    score_a = build_operator_governance_scorecard()
    score_b = build_operator_governance_scorecard()
    assert score_a == score_b
    assert score_a.category in {"BLOCKED", "TRUST_DOWNGRADED", "GOVERNED"}
    assert "override_legitimacy" in score_a.dimensions
    assert "manual_drift_burden" in score_a.dimensions


def test_elegance_regressions_and_invariance_guards() -> None:
    overrides = build_override_report()
    interventions = build_intervention_report()
    traces = build_traceability_report()

    assert len(set(overrides["overrideStates"].values())) <= 6
    assert len(set(interventions["interventionKinds"].values())) <= 7
    assert len(set(traces["traceCompleteness"].values())) <= 2
    assert any(v == "MANUAL_INTERVENTION_ILLEGITIMATE" for v in interventions["interventionLegitimacy"].values())
    assert any(x["scope_state"] == "SCOPE_OVERBROAD" for x in traces["scopeRecords"])
