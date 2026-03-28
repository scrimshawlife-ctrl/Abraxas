from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChangeAdmissionRecord:
    admission_id: str
    change_ref: str
    admission_state: str
    evidence_state: str


@dataclass(frozen=True)
class PromotionGateRecord:
    gate_id: str
    change_ref: str
    promotion_state: str
    gate_reason: str


@dataclass(frozen=True)
class ReleaseReadinessRecord:
    readiness_id: str
    change_ref: str
    readiness_state: str
    readiness_reason: str


@dataclass(frozen=True)
class RejectionRecord:
    rejection_id: str
    change_ref: str
    rejection_state: str
    rejection_reason: str


@dataclass(frozen=True)
class RollbackRecord:
    rollback_id: str
    change_ref: str
    rollback_state: str
    rollback_reason: str


@dataclass(frozen=True)
class AdmissionGovernanceErrorRecord:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class AdmissionGovernanceScorecard:
    artifact_type: str
    artifact_id: str
    dimensions: dict[str, str]
    evidence: dict[str, list[str]]
    blockers: list[str]
    category: str
    scorecard_hash: str
