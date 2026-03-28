from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TimeHorizonRecord:
    horizon_id: str
    entity_ref: str
    horizon_state: str
    cadence_ref: str


@dataclass(frozen=True)
class FreshnessRecord:
    freshness_id: str
    entity_ref: str
    freshness_state: str
    reuse_posture: str


@dataclass(frozen=True)
class DecaySemanticRecord:
    decay_id: str
    entity_ref: str
    decay_state: str
    decay_model: str


@dataclass(frozen=True)
class StalenessRecord:
    staleness_id: str
    entity_ref: str
    staleness_state: str
    operational_validity: str


@dataclass(frozen=True)
class ExpiryRecord:
    expiry_id: str
    entity_ref: str
    expiry_state: str
    expiry_mode: str


@dataclass(frozen=True)
class ArchivalValidityRecord:
    archival_id: str
    entity_ref: str
    archival_state: str
    archival_scope: str


@dataclass(frozen=True)
class FreshnessTransitionRecord:
    transition_id: str
    entity_ref: str
    from_state: str
    to_state: str
    reason: str


@dataclass(frozen=True)
class StaleSupportRecord:
    support_id: str
    entity_ref: str
    support_state: str
    support_surface: str


@dataclass(frozen=True)
class FreshnessGovernanceErrorRecord:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class FreshnessGovernanceScorecard:
    artifact_type: str
    artifact_id: str
    dimensions: dict[str, str]
    evidence: dict[str, list[str]]
    blockers: list[str]
    category: str
    scorecard_hash: str
