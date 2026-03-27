from __future__ import annotations

from abx.docs_governance.docClassification import classify_doc_surfaces, detect_duplicate_doc_surfaces
from abx.docs_governance.docReports import build_doc_audit_report
from abx.docs_governance.docScorecard import build_doc_legibility_scorecard
from abx.docs_governance.freshnessClassification import classify_freshness_states
from abx.docs_governance.freshnessReports import (
    build_doc_freshness_audit_report,
    detect_stale_generated_manual_mismatch,
)
from abx.docs_governance.handoffClassification import classify_handoff_completeness
from abx.docs_governance.handoffReports import build_handoff_audit_report
from abx.docs_governance.roleCoverage import classify_role_legibility
from abx.docs_governance.roleEntrypoints import detect_role_terminology_drift
from abx.docs_governance.roleReports import build_role_legibility_audit_report


def test_doc_surface_governance_stability() -> None:
    assert classify_doc_surfaces() == classify_doc_surfaces()
    assert detect_duplicate_doc_surfaces() == []
    report = build_doc_audit_report()
    assert report == build_doc_audit_report()
    assert report["classification"]["authoritative_reference"]


def test_handoff_completeness_stability() -> None:
    assert classify_handoff_completeness() == classify_handoff_completeness()
    report = build_handoff_audit_report()
    assert report == build_handoff_audit_report()
    assert report["classification"]["stale_handoff"]


def test_role_legibility_stability() -> None:
    assert classify_role_legibility() == classify_role_legibility()
    assert detect_role_terminology_drift() == []
    report = build_role_legibility_audit_report()
    assert report == build_role_legibility_audit_report()
    assert report["coverage"]["fully_legible"]


def test_freshness_and_dependency_stability() -> None:
    assert classify_freshness_states() == classify_freshness_states()
    assert detect_stale_generated_manual_mismatch() == []
    report = build_doc_freshness_audit_report()
    assert report == build_doc_freshness_audit_report()
    assert report["classification"]["stale_candidate"]


def test_documentation_scorecard_determinism_and_blockers() -> None:
    a = build_doc_legibility_scorecard()
    b = build_doc_legibility_scorecard()
    assert a.__dict__ == b.__dict__
    assert "stale_doc_burden" in a.blockers
    assert "handoff_completeness_quality" in a.blockers
