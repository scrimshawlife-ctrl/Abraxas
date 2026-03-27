from __future__ import annotations

from abx.security.abuseReports import build_abuse_path_audit_report
from abx.security.authorityReports import build_authority_boundary_audit_report
from abx.security.integrityReports import build_integrity_audit_report
from abx.security.securityReports import build_security_audit_report
from abx.security.types import SecurityIntegrityScorecard
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_security_integrity_scorecard() -> SecurityIntegrityScorecard:
    security = build_security_audit_report()
    integrity = build_integrity_audit_report()
    abuse = build_abuse_path_audit_report()
    authority = build_authority_boundary_audit_report()

    dimensions = {
        "security_surface_clarity": "GOVERNED" if not security["vocabularyConflicts"] else "PARTIAL",
        "integrity_verification_coverage": "PARTIAL" if integrity["verificationClassification"]["not_computable"] else "GOVERNED",
        "abuse_path_coverage": "PARTIAL" if abuse["containmentClassification"]["partial"] else "GOVERNED",
        "authority_boundary_clarity": "GOVERNED" if not authority["hiddenPrivilegeDrift"] else "PARTIAL",
        "override_waiver_abuse_visibility": "GOVERNED",
        "config_topology_abuse_visibility": "MONITORED",
        "secret_credential_boundary_clarity": "GOVERNED",
        "legacy_exposure_burden": "PARTIAL" if security["classification"]["legacy_redundant_candidate"] else "GOVERNED",
        "containment_recovery_readiness": "PARTIAL" if abuse["containmentClassification"]["partial"] else "GOVERNED",
        "operator_secure_action_legibility": "GOVERNED",
    }
    blockers = sorted(k for k, v in dimensions.items() if v in {"PARTIAL", "HEURISTIC", "NOT_COMPUTABLE"})
    evidence = {
        "security": [security["auditHash"]],
        "integrity": [integrity["auditHash"]],
        "abuse": [abuse["auditHash"]],
        "authority": [authority["auditHash"]],
        "integrityMismatches": [x["verification_id"] for x in integrity["mismatches"]],
        "legacyExposurePaths": [x["abuse_id"] for x in abuse["paths"] if x["exposure_state"] == "legacy_exposure"],
    }
    digest = sha256_bytes(dumps_stable({"dimensions": dimensions, "evidence": evidence, "blockers": blockers}).encode("utf-8"))
    return SecurityIntegrityScorecard(
        artifact_type="SecurityIntegrityScorecard.v1",
        artifact_id="security-integrity-scorecard",
        dimensions=dimensions,
        evidence=evidence,
        blockers=blockers,
        scorecard_hash=digest,
    )
