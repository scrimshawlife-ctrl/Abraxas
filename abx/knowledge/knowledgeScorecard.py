from __future__ import annotations

from abx.knowledge.carryForwardChecks import run_carry_forward_checks
from abx.knowledge.continuityReports import build_continuity_audit_report
from abx.knowledge.forgettingReports import build_forgetting_report
from abx.knowledge.knowledgeReports import build_knowledge_audit_report
from abx.knowledge.memoryLifecycle import build_memory_lifecycle
from abx.knowledge.staleMemoryDetection import detect_stale_memory
from abx.knowledge.types import KnowledgeContinuityScorecard
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_knowledge_continuity_scorecard(run_id: str = "RUN-CONTINUITY") -> KnowledgeContinuityScorecard:
    knowledge = build_knowledge_audit_report()
    continuity = build_continuity_audit_report(run_id=run_id)
    carry = run_carry_forward_checks()
    forgetting = build_forgetting_report()
    stale = detect_stale_memory()

    dimensions = {
        "knowledge_surface_clarity": "GOVERNED",
        "memory_lifecycle_coverage": "GOVERNED" if bool(build_memory_lifecycle()) else "PARTIAL",
        "continuity_linkage_coverage": "GOVERNED" if continuity["coverage"]["complete"] else "PARTIAL",
        "carry_forward_discipline": "GOVERNED" if not carry["staleCarryForward"] else "PARTIAL",
        "forgetting_expiry_visibility": "GOVERNED",
        "stale_memory_burden": "PARTIAL" if stale else "GOVERNED",
        "archival_clarity": "GOVERNED" if forgetting["archivalOnly"] else "PARTIAL",
        "active_vs_historical_quality": "GOVERNED",
    }
    evidence = {
        "knowledge": [knowledge["auditHash"]],
        "continuity": [continuity["auditHash"]],
        "carryForward": ["carry-forward-policy-v1"],
        "forgetting": [forgetting["auditHash"]],
    }
    blockers = sorted([k for k, v in dimensions.items() if v == "PARTIAL"])
    payload = {"dimensions": dimensions, "evidence": evidence, "blockers": blockers}
    digest = sha256_bytes(dumps_stable(payload).encode("utf-8"))
    return KnowledgeContinuityScorecard(
        artifact_type="KnowledgeContinuityScorecard.v1",
        artifact_id=f"knowledge-continuity-scorecard-{run_id}",
        dimensions=dimensions,
        evidence=evidence,
        blockers=blockers,
        scorecard_hash=digest,
    )
