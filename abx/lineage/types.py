from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LineageRecord:
    lineage_id: str
    state_ref: str
    lineage_kind: str
    source_ref: str
    lineage_state: str = "LINEAGE_UNKNOWN"
    lineage_continuity: str = "UNKNOWN"


@dataclass(frozen=True)
class ProvenanceRecord:
    provenance_id: str
    lineage_id: str
    transform_chain: str
    provenance_state: str
    transform_semantics: str = "UNKNOWN"
    upstream_version: str = "UNKNOWN"


@dataclass(frozen=True)
class DerivationRecord:
    derivation_id: str
    provenance_id: str
    derivation_state: str
    stale_state: str
    rederivation_required: str = "NO"


@dataclass(frozen=True)
class MutationLegitimacyRecord:
    legitimacy_id: str
    state_ref: str
    actor: str
    legitimacy_state: str
    mutation_scope: str = "UNKNOWN"
    authority_ref: str = "UNKNOWN"
    mutation_semantics: str = "OVERWRITE"


@dataclass(frozen=True)
class MutationAuthorityRecord:
    authority_id: str
    legitimacy_id: str
    authority_scope: str
    authority_state: str
    policy_ref: str = "UNKNOWN"


@dataclass(frozen=True)
class ReplayabilityRecord:
    replay_id: str
    state_ref: str
    replay_state: str
    reconstructable_state: str
    replay_basis: str = "UNKNOWN"


@dataclass(frozen=True)
class ProvenanceTransitionRecord:
    transition_id: str
    state_ref: str
    from_state: str
    to_state: str
    reason: str
    trust_posture: str = "UNCHANGED"
    action_required: str = "NONE"


@dataclass(frozen=True)
class UnauthorizedMutationRecord:
    unauthorized_id: str
    state_ref: str
    unauthorized_state: str
    response_state: str
    authority_ref: str = "UNKNOWN"
    quarantine_required: str = "NO"


@dataclass(frozen=True)
class LineageGovernanceErrorRecord:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class LineageGovernanceScorecard:
    artifact_type: str
    artifact_id: str
    dimensions: dict[str, str]
    evidence: dict[str, list[str]]
    blockers: list[str]
    category: str
    scorecard_hash: str
