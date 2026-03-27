from __future__ import annotations

from abx.closure.auditReports import build_audit_readiness_record
from abx.closure.closureReports import build_system_closure_record
from abx.closure.exceptionAggregation import build_exception_aggregation_record
from abx.closure.ratificationRecords import build_ratification_decision_record
from abx.closure.types import ClosureRatificationScorecard
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def _scorecard_category(*, closure_state: str, audit_state: str, ratification_state: str) -> str:
    if closure_state in {"BLOCKED", "NOT_COMPUTABLE"}:
        return "BLOCKED"
    if audit_state in {"BLOCKED", "EVIDENCE_INCOMPLETE", "NOT_COMPUTABLE"}:
        return "PARTIAL"
    if ratification_state == "READY_FOR_RATIFICATION" and closure_state == "CLOSURE_COMPLETE":
        return "CLOSED"
    if ratification_state == "CONDITIONALLY_RATIFIABLE" or closure_state == "CLOSURE_COMPLETE_WITH_WAIVERS":
        return "CONDITIONALLY_CLOSED"
    return "PARTIAL"


def build_closure_ratification_scorecard() -> ClosureRatificationScorecard:
    closure = build_system_closure_record()
    audit = build_audit_readiness_record()
    ratification = build_ratification_decision_record()
    exceptions = build_exception_aggregation_record()

    dimensions = {
        "closure_completeness": closure.closure_state,
        "evidence_bundle_readiness": audit.readiness_state,
        "ratification_state": ratification.decision_state,
        "waiver_gap_visibility": "VISIBLE" if closure.waived_domains or exceptions.totals_by_classification else "NO_GAPS",
        "residual_risk_legibility": "VISIBLE" if exceptions.totals_by_classification else "NO_RESIDUALS",
        "blocked_domain_burden": "BLOCKED" if closure.blocked_domains else "CLEAR",
        "stale_evidence_burden": "STALE" if audit.stale_bundles else "FRESH",
        "repeat_audit_ease": "DETERMINISTIC",
        "cross_domain_aggregation_quality": "GOVERNED",
        "operator_acceptance_clarity": "EXPLICIT",
    }
    blockers = sorted(
        [
            key
            for key, value in dimensions.items()
            if value in {"BLOCKED", "STALE", "EVIDENCE_INCOMPLETE", "NOT_COMPUTABLE", "PARTIALLY_CLOSED", "DEGRADED"}
        ]
    )

    evidence = {
        "closure": sorted(closure.evidence_refs),
        "auditBundles": sorted(audit.bundle_states.keys()),
        "ratificationCriteria": sorted(ratification.satisfied_criteria + ratification.unmet_criteria + ratification.waived_criteria),
        "exceptions": sorted(exceptions.totals_by_classification.keys()),
        "blockedDomains": sorted(closure.blocked_domains),
    }
    category = _scorecard_category(
        closure_state=closure.closure_state,
        audit_state=audit.readiness_state,
        ratification_state=ratification.decision_state,
    )
    digest = sha256_bytes(
        dumps_stable({"dimensions": dimensions, "evidence": evidence, "blockers": blockers, "category": category}).encode("utf-8")
    )
    return ClosureRatificationScorecard(
        artifact_type="ClosureRatificationScorecard.v1",
        artifact_id="closure-ratification-scorecard",
        dimensions=dimensions,
        evidence=evidence,
        blockers=blockers,
        category=category,
        scorecard_hash=digest,
    )
