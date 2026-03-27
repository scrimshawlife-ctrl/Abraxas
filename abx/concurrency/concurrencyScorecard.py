from __future__ import annotations

from abx.concurrency.arbitrationReports import build_arbitration_report
from abx.concurrency.concurrentReports import build_concurrent_operation_report
from abx.concurrency.conflictReports import build_conflict_report
from abx.concurrency.overlapReports import build_overlap_resolution_report
from abx.concurrency.types import ConcurrentOperationScorecard
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def _scorecard_category(*, concurrency_posture: str, conflict_posture: str, hidden_winner_risk: bool) -> str:
    if hidden_winner_risk:
        return "HIDDEN_WINNER_RISK"
    if conflict_posture == "BLOCKED_BY_CONFLICT":
        return "BLOCKED"
    if conflict_posture == "ARBITRATION_REQUIRED":
        return "ARBITRATION_READY"
    if concurrency_posture == "CONCURRENCY_READY":
        return "CONCURRENCY_READY"
    if concurrency_posture == "MERGEABLE_CONCURRENT":
        return "MERGE_READY"
    if concurrency_posture == "NOT_COMPUTABLE":
        return "NOT_COMPUTABLE"
    return "PARTIAL"


def build_concurrency_scorecard() -> ConcurrentOperationScorecard:
    concurrent = build_concurrent_operation_report()
    conflict = build_conflict_report()
    arbitration = build_arbitration_report()
    overlap = build_overlap_resolution_report()

    hidden_winner_risk = bool(arbitration["outcomes"].get("NOT_COMPUTABLE"))
    dimensions = {
        "concurrency_domain_clarity": "EXPLICIT",
        "overlap_vs_conflict_quality": "EXPLICIT",
        "conflict_detection_coverage": conflict["posture"],
        "arbitration_decision_clarity": "EXPLICIT",
        "authority_preservation_quality": "PARTIAL" if arbitration["outcomes"].get("ESCALATED") else "GOVERNED",
        "mergeability_discipline": "GOVERNED" if not overlap["resolutions"] else "MONITORED",
        "serialization_hygiene": "SERIALIZATION_HEAVY" if arbitration["outcomes"].get("SERIALIZED") else "BALANCED",
        "hidden_winner_selection_burden": "SUSPECTED" if hidden_winner_risk else "CLEAR",
        "repeated_contention_burden": "ELEVATED" if len(conflict["conflicts"]) >= 3 else "LOW",
        "operator_concurrent_state_clarity": "EXPLICIT",
    }
    blockers = sorted(
        key
        for key, value in dimensions.items()
        if value in {"SUSPECTED", "BLOCKED", "NOT_COMPUTABLE"}
    )
    category = _scorecard_category(
        concurrency_posture=concurrent["posture"],
        conflict_posture=conflict["posture"],
        hidden_winner_risk=hidden_winner_risk,
    )
    evidence = {
        "concurrent": [concurrent["auditHash"]],
        "conflict": [conflict["auditHash"]],
        "arbitration": [arbitration["auditHash"]],
        "overlap": [overlap["auditHash"]],
        "serializedDecisions": arbitration["outcomes"].get("SERIALIZED", []),
        "escalatedDecisions": arbitration["outcomes"].get("ESCALATED", []),
    }
    digest = sha256_bytes(
        dumps_stable({"dimensions": dimensions, "evidence": evidence, "blockers": blockers, "category": category}).encode("utf-8")
    )
    return ConcurrentOperationScorecard(
        artifact_type="ConcurrencyGovernanceScorecard.v1",
        artifact_id="concurrency-governance-scorecard",
        dimensions=dimensions,
        evidence=evidence,
        blockers=blockers,
        category=category,
        scorecard_hash=digest,
    )
