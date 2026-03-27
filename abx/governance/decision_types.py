from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ValueModelRecord:
    value_id: str
    value_term: str
    status: str
    linked_policies: list[str]
    linked_decisions: list[str]
    owner: str


@dataclass(frozen=True)
class PolicySurfaceRecord:
    policy_id: str
    surface: str
    classification: str
    owner: str
    consumed_by: list[str]


@dataclass(frozen=True)
class DecisionOutcomeRecord:
    outcome: str
    completeness: str
    alternatives_rejected: list[str]


@dataclass(frozen=True)
class DecisionRecord:
    decision_id: str
    run_id: str
    policy_refs: list[str]
    value_refs: list[str]
    evidence_refs: list[str]
    trust_state: str
    context_ref: str
    outcome: DecisionOutcomeRecord


@dataclass(frozen=True)
class OverrideRecord:
    override_id: str
    override_type: str
    owner: str
    reason: str
    scope: str
    duration: str
    target_policy: str


@dataclass(frozen=True)
class OverridePrecedenceRecord:
    precedence_id: str
    order: list[str]
    hidden_override_detected: bool


@dataclass(frozen=True)
class PolicyCoverageRecord:
    policy_id: str
    coverage: str


@dataclass(frozen=True)
class DecisionCoverageRecord:
    decision_id: str
    coverage: str


@dataclass(frozen=True)
class DecisionGovernanceErrorRecord:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class DecisionGovernanceScorecard:
    artifact_type: str
    artifact_id: str
    dimensions: dict[str, str]
    evidence: dict[str, list[str]]
    blockers: list[str]
    scorecard_hash: str
