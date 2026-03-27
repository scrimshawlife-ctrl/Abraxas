from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExperimentSurfaceRecord:
    experiment_id: str
    capability: str
    surface_kind: str
    runtime_scope: str
    influence_boundary: str
    owner: str
    governance_layers: list[str]


@dataclass(frozen=True)
class HypothesisRecord:
    hypothesis_id: str
    experiment_id: str
    statement: str
    expected_signal: str
    baseline_ref: str
    success_criteria: list[str]


@dataclass(frozen=True)
class ExperimentConditionRecord:
    condition_id: str
    experiment_id: str
    method: str
    config_ref: str
    dataset_ref: str
    run_envelope: str


@dataclass(frozen=True)
class ExperimentOutcomeRecord:
    outcome_id: str
    experiment_id: str
    observed_signal: str
    outcome_class: str
    comparison_result: str
    evidence_refs: list[str]


@dataclass(frozen=True)
class InnovationLifecycleRecord:
    lifecycle_id: str
    experiment_id: str
    state: str
    next_gate: str
    blockers: list[str]


@dataclass(frozen=True)
class PromotionReadinessRecord:
    readiness_id: str
    experiment_id: str
    readiness_state: str
    required_evidence: list[str]
    missing_evidence: list[str]


@dataclass(frozen=True)
class RetirementRecord:
    retirement_id: str
    experiment_id: str
    recommendation: str
    reason: str
    archive_ref: str


@dataclass(frozen=True)
class InnovationPortfolioRecord:
    portfolio_id: str
    experiment_id: str
    portfolio_class: str
    relevance: str
    maintenance_burden: str
    promotion_potential: str


@dataclass(frozen=True)
class ExperimentGovernanceErrorRecord:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class ExperimentationGovernanceScorecard:
    artifact_type: str
    artifact_id: str
    dimensions: dict[str, str]
    evidence: dict[str, list[str]]
    blockers: list[str]
    scorecard_hash: str
