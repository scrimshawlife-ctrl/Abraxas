from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResourceReservationRecord:
    reservation_id: str
    resource_ref: str
    reservation_state: str
    actor_ref: str


@dataclass(frozen=True)
class CapacityCommitmentRecord:
    commitment_id: str
    resource_ref: str
    commitment_state: str
    commitment_reason: str


@dataclass(frozen=True)
class AllocationRecord:
    allocation_id: str
    resource_ref: str
    allocation_state: str
    allocation_reason: str


@dataclass(frozen=True)
class ContentionBudgetRecord:
    budget_id: str
    resource_ref: str
    contention_state: str
    budget_state: str


@dataclass(frozen=True)
class OvercommitmentRecord:
    overcommitment_id: str
    resource_ref: str
    overcommitment_state: str
    overcommitment_reason: str


@dataclass(frozen=True)
class StarvationRiskRecord:
    starvation_id: str
    resource_ref: str
    starvation_state: str
    starvation_reason: str


@dataclass(frozen=True)
class CapacityTransitionRecord:
    transition_id: str
    resource_ref: str
    from_state: str
    to_state: str
    reason: str


@dataclass(frozen=True)
class BudgetExhaustionRecord:
    exhaustion_id: str
    resource_ref: str
    exhaustion_state: str
    exhaustion_reason: str


@dataclass(frozen=True)
class CapacityGovernanceErrorRecord:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class CapacityGovernanceScorecard:
    artifact_type: str
    artifact_id: str
    dimensions: dict[str, str]
    evidence: dict[str, list[str]]
    blockers: list[str]
    category: str
    scorecard_hash: str
