from __future__ import annotations

from abx.docs_governance.docReports import build_doc_audit_report
from abx.docs_governance.freshnessReports import build_doc_freshness_audit_report
from abx.docs_governance.handoffReports import build_handoff_audit_report
from abx.docs_governance.roleReports import build_role_legibility_audit_report
from abx.docs_governance.types import DocumentationLegibilityScorecard
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_doc_legibility_scorecard() -> DocumentationLegibilityScorecard:
    docs = build_doc_audit_report()
    handoff = build_handoff_audit_report()
    roles = build_role_legibility_audit_report()
    freshness = build_doc_freshness_audit_report()

    dimensions = {
        "documentation_surface_clarity": "GOVERNED" if not docs["duplicates"] else "PARTIAL",
        "duplication_burden": "PARTIAL" if docs["classification"]["legacy_redundant_candidate"] else "GOVERNED",
        "handoff_completeness_quality": "PARTIAL" if handoff["classification"]["partial_handoff"] else "MAINTAINED",
        "role_based_legibility": "PARTIAL" if roles["coverage"]["partial"] else "GOVERNED",
        "freshness_staleness_visibility": "GOVERNED",
        "canonical_linkage_quality": "GOVERNED",
        "stale_doc_burden": "STALE_PRONE" if freshness["classification"]["stale_candidate"] else "MAINTAINED",
        "generated_manual_alignment": "GOVERNED" if not freshness["staleGeneratedMismatch"] else "PARTIAL",
        "onboarding_friendliness": "MONITORED",
        "organizational_transfer_readiness": "PARTIAL" if handoff["classification"]["stale_handoff"] else "MAINTAINED",
    }
    blockers = sorted(k for k, v in dimensions.items() if v in {"PARTIAL", "BLOCKED", "NOT_COMPUTABLE", "STALE_PRONE"})
    evidence = {
        "docs": [docs["auditHash"]],
        "handoff": [handoff["auditHash"]],
        "roles": [roles["auditHash"]],
        "freshness": [freshness["auditHash"]],
        "staleDocs": freshness["classification"]["stale_candidate"],
        "staleHandoffs": handoff["classification"]["stale_handoff"],
    }
    digest = sha256_bytes(dumps_stable({"dimensions": dimensions, "evidence": evidence, "blockers": blockers}).encode("utf-8"))
    return DocumentationLegibilityScorecard(
        artifact_type="DocumentationLegibilityScorecard.v1",
        artifact_id="documentation-legibility-scorecard",
        dimensions=dimensions,
        evidence=evidence,
        blockers=blockers,
        scorecard_hash=digest,
    )
