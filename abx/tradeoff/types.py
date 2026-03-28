from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ValueWeightingRecord:
    weighting_id: str
    decision_ref: str
    weighting_state: str
    weighting_source: str
    dominant_objective: str


@dataclass(frozen=True)
class PriorityAssignmentRecord:
    priority_id: str
    decision_ref: str
    priority_state: str
    rank: int
    tie_breaker: str


@dataclass(frozen=True)
class TradeoffRecord:
    tradeoff_id: str
    decision_ref: str
    tradeoff_state: str
    gain_objective: str
    sacrifice_objective: str


@dataclass(frozen=True)
class SacrificeRecord:
    sacrifice_id: str
    decision_ref: str
    sacrifice_state: str
    sacrifice_scope: str


@dataclass(frozen=True)
class PriorityOverrideRecord:
    override_id: str
    decision_ref: str
    override_state: str
    override_reason: str


@dataclass(frozen=True)
class ObjectiveConflictRecord:
    conflict_id: str
    decision_ref: str
    conflict_state: str
    resolution_state: str


@dataclass(frozen=True)
class ValueDriftRecord:
    drift_id: str
    decision_ref: str
    drift_state: str
    drift_signal: str


@dataclass(frozen=True)
class WeightingTransitionRecord:
    transition_id: str
    decision_ref: str
    from_state: str
    to_state: str
    reason: str


@dataclass(frozen=True)
class TradeoffGovernanceErrorRecord:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class TradeoffGovernanceScorecard:
    artifact_type: str
    artifact_id: str
    dimensions: dict[str, str]
    evidence: dict[str, list[str]]
    blockers: list[str]
    category: str
    scorecard_hash: str
