from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HumanApprovalRecord:
    approval_id: str
    action_class: str
    scope_ref: str
    approval_required: str
    requested_by: str
    approver_id: str
    requested_at: str
    valid_until: str
    raw_signal: str


@dataclass(frozen=True)
class ConsentStateRecord:
    consent_id: str
    approval_id: str
    consent_state: str
    evidence_ref: str


@dataclass(frozen=True)
class AuthorityToProceedRecord:
    authority_id: str
    approval_id: str
    actor_id: str
    actor_role: str
    approved_scope: str
    attempted_scope: str
    valid_until: str


@dataclass(frozen=True)
class ApproverValidityRecord:
    validity_id: str
    authority_id: str
    validity_state: str
    reason: str


@dataclass(frozen=True)
class ApprovalTransitionRecord:
    transition_id: str
    approval_id: str
    from_state: str
    to_state: str
    reason: str


@dataclass(frozen=True)
class DelegatedApprovalRecord:
    delegation_id: str
    approval_id: str
    delegated_by: str
    delegated_to: str
    delegated_scope: str
    delegation_valid_until: str
    delegation_state: str


@dataclass(frozen=True)
class RevokedApprovalRecord:
    revocation_id: str
    approval_id: str
    revocation_state: str
    reason: str


@dataclass(frozen=True)
class ExpiredApprovalRecord:
    expiry_id: str
    approval_id: str
    expiry_state: str
    expired_at: str


@dataclass(frozen=True)
class ApprovalGovernanceErrorRecord:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class ApprovalGovernanceScorecard:
    artifact_type: str
    artifact_id: str
    dimensions: dict[str, str]
    evidence: dict[str, list[str]]
    blockers: list[str]
    category: str
    scorecard_hash: str
