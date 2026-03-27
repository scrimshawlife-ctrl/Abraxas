from __future__ import annotations

from abx.security.abuseClassification import classify_abuse_paths, detect_inconsistent_abuse_taxonomy
from abx.security.abuseContainment import classify_abuse_containment, validate_containment_linkage
from abx.security.abuseReports import build_abuse_path_audit_report
from abx.security.actionBoundaries import (
    classify_action_permissions,
    classify_authority_boundaries,
    detect_redundant_authority_models,
)
from abx.security.authorityPrecedence import build_authority_precedence, detect_hidden_privilege_drift
from abx.security.authorityReports import build_authority_boundary_audit_report
from abx.security.integrityReports import build_integrity_audit_report
from abx.security.integrityVerification import classify_integrity_verification, detect_integrity_mismatches
from abx.security.securityClassification import classify_security_surfaces, detect_duplicate_security_vocabulary
from abx.security.securityReports import build_security_audit_report
from abx.security.securityScorecard import build_security_integrity_scorecard


def test_security_surface_classification_and_report_determinism() -> None:
    assert classify_security_surfaces() == classify_security_surfaces()
    assert detect_duplicate_security_vocabulary() == []
    report_a = build_security_audit_report()
    report_b = build_security_audit_report()
    assert report_a == report_b
    assert report_a["classification"]["critical"]


def test_integrity_verification_and_tamper_visibility_stability() -> None:
    assert classify_integrity_verification() == classify_integrity_verification()
    mismatches = detect_integrity_mismatches()
    assert mismatches == detect_integrity_mismatches()
    assert any(x["reason"] == "weak_integrity_assurance" for x in mismatches)
    report = build_integrity_audit_report()
    assert report == build_integrity_audit_report()
    assert report["tamperClassification"]["governed"]


def test_abuse_path_containment_and_taxonomy_stability() -> None:
    assert classify_abuse_paths() == classify_abuse_paths()
    assert classify_abuse_containment() == classify_abuse_containment()
    assert validate_containment_linkage() == []
    assert detect_inconsistent_abuse_taxonomy() == []
    report = build_abuse_path_audit_report()
    assert report == build_abuse_path_audit_report()


def test_authority_boundary_precedence_and_drift_checks() -> None:
    assert classify_authority_boundaries() == classify_authority_boundaries()
    assert classify_action_permissions() == classify_action_permissions()
    assert build_authority_precedence() == build_authority_precedence()
    assert detect_hidden_privilege_drift() == []
    assert detect_redundant_authority_models() == []
    report = build_authority_boundary_audit_report()
    assert report == build_authority_boundary_audit_report()


def test_security_integrity_scorecard_determinism_and_blockers() -> None:
    a = build_security_integrity_scorecard()
    b = build_security_integrity_scorecard()
    assert a.__dict__ == b.__dict__
    assert "integrity_verification_coverage" in a.blockers
    assert "legacy_exposure_burden" in a.blockers
