from __future__ import annotations

from abx.closure.auditReports import build_audit_readiness_record, build_audit_readiness_report
from abx.closure.closureClassification import CLOSURE_STATES, classify_system_closure_state
from abx.closure.closureDependencies import build_closure_dependencies
from abx.closure.closureReports import build_system_closure_record, build_system_closure_report
from abx.closure.closureScorecard import build_closure_ratification_scorecard
from abx.closure.evidenceBundles import build_evidence_bundles
from abx.closure.exceptionAggregation import build_exception_aggregation_record
from abx.closure.gapReports import build_residual_gap_report
from abx.closure.nonClosureRecords import build_non_closure_records
from abx.closure.ratificationCriteria import build_ratification_criteria
from abx.closure.ratificationRecords import build_ratification_decision_record
from abx.closure.ratificationReports import build_ratification_report


def test_closure_surface_classification_dependency_and_report_determinism() -> None:
    closure_a = build_system_closure_record()
    closure_b = build_system_closure_record()
    assert closure_a == closure_b
    assert closure_a.closure_state in CLOSURE_STATES

    deps_a = build_closure_dependencies()
    deps_b = build_closure_dependencies()
    assert deps_a == deps_b

    report_a = build_system_closure_report()
    report_b = build_system_closure_report()
    assert report_a == report_b
    assert classify_system_closure_state(closure_a.domain_states, closure_a.dependency_states) == closure_a.closure_state


def test_audit_bundle_assembly_completeness_and_reporting_are_deterministic() -> None:
    bundles_a = build_evidence_bundles()
    bundles_b = build_evidence_bundles()
    assert bundles_a == bundles_b
    assert bundles_a

    readiness_a = build_audit_readiness_record()
    readiness_b = build_audit_readiness_record()
    assert readiness_a == readiness_b

    report_a = build_audit_readiness_report()
    report_b = build_audit_readiness_report()
    assert report_a == report_b
    assert set(readiness_a.bundle_states).issubset({b.bundle_id for b in bundles_a})


def test_ratification_criteria_status_scope_linkage_and_reporting_are_deterministic() -> None:
    criteria_a = build_ratification_criteria()
    criteria_b = build_ratification_criteria()
    assert criteria_a == criteria_b
    assert all(c.scope for c in criteria_a)

    decision_a = build_ratification_decision_record()
    decision_b = build_ratification_decision_record()
    assert decision_a == decision_b
    assert sorted(decision_a.evidence_bundle_ids)

    report_a = build_ratification_report()
    report_b = build_ratification_report()
    assert report_a == report_b
    assert report_a["decision"]["scope"] == "baseline"


def test_residual_gap_and_non_closure_visibility_are_deterministic() -> None:
    non_closure_a = build_non_closure_records()
    non_closure_b = build_non_closure_records()
    assert non_closure_a == non_closure_b
    assert all(x.classification in {"waived", "blocking", "stale_exception", "unresolved"} for x in non_closure_a)

    aggregation_a = build_exception_aggregation_record()
    aggregation_b = build_exception_aggregation_record()
    assert aggregation_a == aggregation_b

    gap_report_a = build_residual_gap_report()
    gap_report_b = build_residual_gap_report()
    assert gap_report_a == gap_report_b


def test_closure_ratification_scorecard_determinism_and_blocker_surfacing() -> None:
    score_a = build_closure_ratification_scorecard()
    score_b = build_closure_ratification_scorecard()
    assert score_a == score_b
    assert score_a.category in {"CLOSED", "CONDITIONALLY_CLOSED", "PARTIAL", "BLOCKED"}
    assert "closure_completeness" in score_a.dimensions
    assert "operator_acceptance_clarity" in score_a.dimensions


def test_elegance_regressions_and_invariance_guards() -> None:
    closure = build_system_closure_record()
    audit = build_audit_readiness_record()
    decision = build_ratification_decision_record()
    non_closure = build_non_closure_records()

    # Duplicate closure vocabulary detection.
    assert len(set(closure.domain_states.values()) - CLOSURE_STATES) == 0

    # Redundant evidence-bundle grammar detection (single bundle-state grammar only).
    assert set(audit.bundle_states.values()).issubset({"AUDIT_READY", "AUDIT_READY_WITH_GAPS", "EVIDENCE_INCOMPLETE", "STALE_EVIDENCE", "BLOCKED"})

    # Hidden-ratification-threshold drift detection (criteria are always explicit).
    assert decision.satisfied_criteria or decision.unmet_criteria or decision.waived_criteria

    # Unresolved-gap masking detection.
    if closure.blocked_domains:
        assert any(x.classification == "blocking" for x in non_closure)
