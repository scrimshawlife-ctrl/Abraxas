from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IdentityResolutionRecord:
    resolution_id: str
    reference_ref: str
    resolution_state: str
    canonical_entity: str


@dataclass(frozen=True)
class CanonicalReferenceRecord:
    canonical_id: str
    entity_ref: str
    canonical_state: str
    canonical_source: str


@dataclass(frozen=True)
class EntityPersistenceRecord:
    persistence_id: str
    entity_ref: str
    persistence_state: str
    continuity_ref: str


@dataclass(frozen=True)
class AliasRecord:
    alias_id: str
    entity_ref: str
    alias_ref: str
    alias_state: str


@dataclass(frozen=True)
class MergeRecord:
    merge_id: str
    source_entity: str
    target_entity: str
    merge_state: str


@dataclass(frozen=True)
class SplitRecord:
    split_id: str
    source_entity: str
    child_entity: str
    split_state: str


@dataclass(frozen=True)
class ReferentialCoherenceRecord:
    coherence_id: str
    entity_ref: str
    coherence_state: str
    downstream_state: str


@dataclass(frozen=True)
class ReferenceMismatchRecord:
    mismatch_id: str
    reference_ref: str
    mismatch_state: str
    mismatch_reason: str


@dataclass(frozen=True)
class IdentityGovernanceErrorRecord:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class IdentityGovernanceScorecard:
    artifact_type: str
    artifact_id: str
    dimensions: dict[str, str]
    evidence: dict[str, list[str]]
    blockers: list[str]
    category: str
    scorecard_hash: str
