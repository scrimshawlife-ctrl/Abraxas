from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CanonSurfaceRecord:
    canon_id: str
    surface_ref: str
    canon_class: str
    domain_refs: list[str]
    interpretation_boundary: str
    owner: str


@dataclass(frozen=True)
class GovernanceChangeRecord:
    change_id: str
    title: str
    change_class: str
    affected_domains: list[str]
    state: str
    proposer: str


@dataclass(frozen=True)
class SelfModificationRecord:
    record_id: str
    change_id: str
    self_mod_kind: str
    risk_level: str
    preconditions: list[str]


@dataclass(frozen=True)
class StewardshipRecord:
    steward_id: str
    steward_role: str
    domains: list[str]
    authority_level: str
    status: str


@dataclass(frozen=True)
class AuthorityOfChangeRecord:
    authority_id: str
    change_id: str
    approver_role: str
    review_chain: list[str]
    escalation_path: str


@dataclass(frozen=True)
class SupersessionRecord:
    supersession_id: str
    superseded_ref: str
    active_ref: str
    reason: str
    impacted_domains: list[str]


@dataclass(frozen=True)
class CanonConflictRecord:
    conflict_id: str
    left_ref: str
    right_ref: str
    conflict_state: str
    resolution_ref: str


@dataclass(frozen=True)
class CanonCompressionRecord:
    compression_id: str
    source_refs: list[str]
    merged_ref: str
    compression_state: str


@dataclass(frozen=True)
class MetaGovernanceErrorRecord:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class MetaGovernanceScorecard:
    artifact_type: str
    artifact_id: str
    dimensions: dict[str, str]
    evidence: dict[str, list[str]]
    blockers: list[str]
    scorecard_hash: str
