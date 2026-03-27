from __future__ import annotations

from abx.meta.canonClassification import classify_canon_surfaces, detect_canon_taxonomy_drift, detect_duplicate_canon_home
from abx.meta.canonReports import build_canon_audit_report
from abx.meta.canonResolutionReports import (
    build_canon_conflict_audit_report,
    classify_conflict_and_supersession,
    detect_unresolved_supersession_drift,
)
from abx.meta.changeClassification import classify_governance_changes, detect_change_taxonomy_drift, detect_hidden_meta_change
from abx.meta.changeReports import build_governance_change_audit_report
from abx.meta.metaScorecard import build_meta_governance_scorecard
from abx.meta.stewardshipReports import (
    build_stewardship_audit_report,
    classify_stewardship_roles,
    detect_hidden_meta_authority,
)


def test_canon_surface_governance_determinism() -> None:
    assert classify_canon_surfaces() == classify_canon_surfaces()
    assert detect_canon_taxonomy_drift() == []
    assert detect_duplicate_canon_home() == []
    report_a = build_canon_audit_report()
    report_b = build_canon_audit_report()
    assert report_a == report_b
    assert report_a["classification"]["authoritative_canon"]


def test_governance_change_and_self_modification_determinism() -> None:
    assert classify_governance_changes() == classify_governance_changes()
    assert detect_change_taxonomy_drift() == []
    hidden = detect_hidden_meta_change()
    assert hidden == detect_hidden_meta_change()
    assert any(x["reason"] == "canon_impact_not_approved" for x in hidden)
    report = build_governance_change_audit_report()
    assert report == build_governance_change_audit_report()
    assert report["selfModification"]


def test_stewardship_authority_determinism() -> None:
    assert classify_stewardship_roles() == classify_stewardship_roles()
    hidden = detect_hidden_meta_authority()
    assert hidden == detect_hidden_meta_authority()
    assert hidden
    report = build_stewardship_audit_report()
    assert report == build_stewardship_audit_report()
    assert report["classification"]["canonical_steward"]


def test_conflict_supersession_compression_determinism() -> None:
    assert classify_conflict_and_supersession() == classify_conflict_and_supersession()
    unresolved = detect_unresolved_supersession_drift()
    assert unresolved == detect_unresolved_supersession_drift()
    assert unresolved
    report = build_canon_conflict_audit_report()
    assert report == build_canon_conflict_audit_report()
    assert report["classification"]["superseded"]


def test_meta_governance_scorecard_determinism_and_blockers() -> None:
    a = build_meta_governance_scorecard()
    b = build_meta_governance_scorecard()
    assert a.__dict__ == b.__dict__
    assert "governance_change_traceability" in a.blockers
    assert "stewardship_clarity" in a.blockers
    assert "supersession_conflict_visibility" in a.blockers
