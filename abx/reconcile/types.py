from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StateConflictRecord:
    conflict_id: str
    left_surface: str
    right_surface: str
    conflict_state: str
    severity: str


@dataclass(frozen=True)
class ReconciliationRecord:
    reconciliation_id: str
    conflict_ref: str
    repair_mode: str
    reconciliation_state: str


@dataclass(frozen=True)
class RepairLegitimacyRecord:
    legitimacy_id: str
    reconciliation_ref: str
    legitimacy_state: str
    legitimacy_reason: str


@dataclass(frozen=True)
class RestorationStatusRecord:
    restoration_id: str
    reconciliation_ref: str
    restoration_state: str
    validation_state: str


@dataclass(frozen=True)
class AuthoritativeSourceRecord:
    authority_id: str
    conflict_ref: str
    authority_state: str
    authority_source: str


@dataclass(frozen=True)
class LossyRepairRecord:
    loss_id: str
    reconciliation_ref: str
    loss_state: str
    loss_reason: str


@dataclass(frozen=True)
class CosmeticAlignmentRecord:
    cosmetic_id: str
    reconciliation_ref: str
    cosmetic_state: str
    cosmetic_surface: str


@dataclass(frozen=True)
class ConsistencyTransitionRecord:
    transition_id: str
    reconciliation_ref: str
    from_state: str
    to_state: str
    reason: str


@dataclass(frozen=True)
class ReconciliationGovernanceErrorRecord:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class ReconciliationGovernanceScorecard:
    artifact_type: str
    artifact_id: str
    dimensions: dict[str, str]
    evidence: dict[str, list[str]]
    blockers: list[str]
    category: str
    scorecard_hash: str
