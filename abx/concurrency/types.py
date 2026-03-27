from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ConcurrentOperationRecord:
    operation_id: str
    actor_id: str
    target_ref: str
    domain_id: str
    action_class: str
    authority_scope: str
    side_effect_level: str


@dataclass(frozen=True)
class ConcurrencyDomainRecord:
    domain_id: str
    overlap_policy: str
    owner: str
    shared_resources: list[str]


@dataclass(frozen=True)
class ConflictRecord:
    conflict_id: str
    left_operation_id: str
    right_operation_id: str
    conflict_class: str
    phase: str
    evidence_ref: str


@dataclass(frozen=True)
class ConflictClassificationRecord:
    classification_id: str
    conflict_id: str
    classification: str
    resolution_hint: str


@dataclass(frozen=True)
class ArbitrationDecisionRecord:
    decision_id: str
    conflict_id: str
    outcome: str
    winner_operation_id: str
    loser_operation_id: str
    rationale: str


@dataclass(frozen=True)
class OverlapResolutionRecord:
    resolution_id: str
    conflict_id: str
    outcome_class: str
    execution_mode: str
    safety_state: str


@dataclass(frozen=True)
class MergeabilityRecord:
    mergeability_id: str
    left_operation_id: str
    right_operation_id: str
    merge_state: str
    reason: str


@dataclass(frozen=True)
class SerializationPolicyRecord:
    policy_id: str
    domain_id: str
    trigger_classes: list[str]
    strategy: str


@dataclass(frozen=True)
class CompensationRecord:
    compensation_id: str
    conflict_id: str
    compensation_class: str
    required: bool
    reason: str


@dataclass(frozen=True)
class ConcurrencyGovernanceErrorRecord:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class ConcurrentOperationScorecard:
    artifact_type: str
    artifact_id: str
    dimensions: dict[str, str]
    evidence: dict[str, list[str]]
    blockers: list[str]
    category: str
    scorecard_hash: str
