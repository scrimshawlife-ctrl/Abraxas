from __future__ import annotations

from abx.approval.approvalReports import build_human_approval_report
from abx.approval.authorityReports import build_authority_report
from abx.approval.consentReports import build_consent_state_report
from abx.approval.transitionReports import build_approval_transition_report
from abx.approval.types import ApprovalGovernanceScorecard
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


ALLOWED_APPROVAL_STATES = {
    "APPROVAL_REQUIRED",
    "APPROVAL_REQUESTED",
    "APPROVAL_GRANTED",
    "APPROVAL_CONDITIONAL",
    "APPROVAL_DENIED",
    "APPROVAL_WITHDRAWN",
    "APPROVAL_EXPIRED",
    "INVALID_APPROVAL",
    "BLOCKED_PENDING_APPROVAL",
    "NOT_COMPUTABLE",
}


def _category(*, blocked: bool, stale: bool, ambiguous: bool, invalid_authority: bool) -> str:
    if blocked or invalid_authority:
        return "BLOCKED"
    if stale:
        return "STALE_APPROVAL_BURDENED"
    if ambiguous:
        return "AMBIGUITY_BURDENED"
    return "APPROVAL_READY"


def build_approval_governance_scorecard() -> ApprovalGovernanceScorecard:
    approval = build_human_approval_report()
    consent = build_consent_state_report()
    authority = build_authority_report()
    transitions = build_approval_transition_report()

    blocked = any(v in {"BLOCKED_PENDING_APPROVAL", "APPROVAL_DENIED"} for v in approval["approvalStates"].values())
    stale = any(v in {"APPROVAL_EXPIRED", "EXPIRED_CONSENT"} for v in [*approval["approvalStates"].values(), *consent["consentClassification"].values()])
    ambiguous = any(v in {"AMBIGUOUS_CONSENT", "ACKNOWLEDGMENT_ONLY"} for v in consent["consentClassification"].values())
    invalid_authority = any(v["validity_state"] in {"INVALID_AUTHORITY", "SCOPE_INVALID_AUTHORITY", "EXPIRED_AUTHORITY"} for v in authority["validityRecords"])

    dimensions = {
        "approval_state_clarity": "EXPLICIT" if set(approval["approvalStates"].values()).issubset(ALLOWED_APPROVAL_STATES) else "NOT_COMPUTABLE",
        "consent_explicitness_quality": "AMBIGUOUS" if ambiguous else "CLEAR",
        "authority_validity_quality": "INVALID_PRESENT" if invalid_authority else "VALID",
        "withdrawal_expiry_denial_visibility": "VISIBLE",
        "delegation_boundary_quality": "BOUNDED" if all(x["delegation_state"] == "AUTHORITY_DELEGATED" for x in transitions["delegated"][:1]) else "PARTIAL",
        "stale_approval_burden": "ELEVATED" if stale else "LOW",
        "blocked_pending_approval_visibility": "VISIBLE" if blocked else "LOW",
        "ambiguity_burden": "ELEVATED" if ambiguous else "LOW",
        "reapproval_discipline": "ENFORCED" if any(x["to_state"] == "APPROVAL_EXPIRED" for x in transitions["transitions"]) else "PARTIAL",
        "operator_permission_clarity": "EXPLICIT",
    }
    blockers = sorted(k for k, v in dimensions.items() if v in {"NOT_COMPUTABLE", "AMBIGUOUS", "INVALID_PRESENT", "ELEVATED"})
    evidence = {
        "approval": [approval["auditHash"]],
        "consent": [consent["auditHash"]],
        "authority": [authority["auditHash"]],
        "transitions": [transitions["auditHash"]],
    }
    category = _category(blocked=blocked, stale=stale, ambiguous=ambiguous, invalid_authority=invalid_authority)
    scorecard_hash = sha256_bytes(dumps_stable({"dimensions": dimensions, "evidence": evidence, "blockers": blockers, "category": category}).encode("utf-8"))
    return ApprovalGovernanceScorecard(
        artifact_type="ApprovalGovernanceScorecard.v1",
        artifact_id="approval-governance-scorecard",
        dimensions=dimensions,
        evidence=evidence,
        blockers=blockers,
        category=category,
        scorecard_hash=scorecard_hash,
    )
