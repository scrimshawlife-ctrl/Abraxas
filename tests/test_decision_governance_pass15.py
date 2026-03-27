from __future__ import annotations

from abx.decision.decisionClassification import classify_decision_completeness
from abx.decision.decisionCoverage import build_decision_coverage
from abx.decision.decisionRecords import build_decision_records
from abx.decision.decisionSerialization import serialize_decisions
from abx.governance.decisionScorecard import build_decision_governance_scorecard
from abx.governance.overrideClassification import classify_overrides, detect_stale_overrides
from abx.governance.overridePrecedence import build_override_precedence
from abx.governance.overrideReports import build_override_audit_report
from abx.governance.policyClassification import classify_policy_surfaces, detect_duplicate_policy_surfaces
from abx.governance.policyReports import build_policy_audit_report
from abx.governance.valueClassification import classify_values, detect_overlapping_value_terms
from abx.governance.valueReports import build_value_audit_report


def test_value_model_classification_and_overlap_stability() -> None:
    a = classify_values()
    b = classify_values()
    assert a == b
    assert detect_overlapping_value_terms() == []

    r1 = build_value_audit_report()
    r2 = build_value_audit_report()
    assert r1 == r2


def test_policy_surface_governance_stability() -> None:
    a = classify_policy_surfaces()
    b = classify_policy_surfaces()
    assert a == b
    assert detect_duplicate_policy_surfaces() == []

    report = build_policy_audit_report()
    assert report["artifactType"] == "PolicySurfaceAudit.v1"


def test_decision_records_are_typed_and_serializable() -> None:
    rows = build_decision_records(run_id="RUN-1")
    assert rows
    assert all(row.policy_refs and row.value_refs and row.evidence_refs for row in rows)

    cov = build_decision_coverage(run_id="RUN-1")
    assert all(x.coverage in {"COVERED", "PARTIAL"} for x in cov)

    completeness = classify_decision_completeness(run_id="RUN-1")
    assert "fully_governed" in completeness
    assert serialize_decisions(run_id="RUN-1") == serialize_decisions(run_id="RUN-1")


def test_override_classification_precedence_and_reports() -> None:
    classes = classify_overrides()
    assert "emergency_override" in classes
    assert detect_stale_overrides() == []

    precedence = build_override_precedence()
    assert precedence.order[0] == "authoritative_policy"
    assert precedence.hidden_override_detected is False

    a = build_override_audit_report()
    b = build_override_audit_report()
    assert a == b


def test_decision_governance_scorecard_determinism_and_blockers() -> None:
    a = build_decision_governance_scorecard(run_id="RUN-1")
    b = build_decision_governance_scorecard(run_id="RUN-1")
    assert a.__dict__ == b.__dict__
    assert isinstance(a.blockers, list)
