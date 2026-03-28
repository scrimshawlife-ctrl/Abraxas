from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SemanticDriftRecord:
    drift_id: str
    entity_ref: str
    drift_kind: str
    drift_state: str
    evidence_ref: str


@dataclass(frozen=True)
class SchemaEvolutionRecord:
    evolution_id: str
    schema_ref: str
    from_version: str
    to_version: str
    structural_compatibility: str
    semantic_compatibility: str


@dataclass(frozen=True)
class CompatibilitySemanticRecord:
    compatibility_id: str
    evolution_id: str
    compatibility_state: str
    adapter_state: str
    migration_required: str


@dataclass(frozen=True)
class MeaningPreservationRecord:
    preservation_id: str
    entity_ref: str
    preservation_state: str
    migration_state: str
    translation_required: str


@dataclass(frozen=True)
class SemanticAliasRecord:
    alias_id: str
    canonical_ref: str
    alias_ref: str
    alias_state: str


@dataclass(frozen=True)
class DeprecatedMeaningRecord:
    deprecation_id: str
    entity_ref: str
    deprecation_state: str
    downstream_risk: str


@dataclass(frozen=True)
class SemanticTransitionRecord:
    transition_id: str
    entity_ref: str
    from_state: str
    to_state: str
    reason: str
    trust_posture: str


@dataclass(frozen=True)
class ReinterpretationRiskRecord:
    risk_id: str
    entity_ref: str
    risk_state: str
    interpretation_state: str


@dataclass(frozen=True)
class SemanticGovernanceErrorRecord:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class SemanticGovernanceScorecard:
    artifact_type: str
    artifact_id: str
    dimensions: dict[str, str]
    evidence: dict[str, list[str]]
    blockers: list[str]
    category: str
    scorecard_hash: str
