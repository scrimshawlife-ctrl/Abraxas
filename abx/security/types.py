from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SecuritySurfaceRecord:
    surface_id: str
    workflow: str
    capability: str
    environment_scope: str
    criticality: str
    security_domain: str
    authority_class: str
    owner: str


@dataclass(frozen=True)
class IntegrityVerificationRecord:
    verification_id: str
    target_surface: str
    artifact_class: str
    verification_mode: str
    status: str
    owner: str


@dataclass(frozen=True)
class TamperResistanceRecord:
    tamper_id: str
    target_surface: str
    protection_class: str
    resistance_level: str
    mismatch_signal: str
    owner: str


@dataclass(frozen=True)
class AbusePathRecord:
    abuse_id: str
    abuse_class: str
    entry_surface: str
    target_surface: str
    exposure_state: str
    owner: str


@dataclass(frozen=True)
class AbuseContainmentRecord:
    containment_id: str
    abuse_id: str
    control_surface: str
    control_mode: str
    status: str
    recovery_path: str


@dataclass(frozen=True)
class AuthorityBoundaryRecord:
    boundary_id: str
    actor: str
    action_class: str
    scope: str
    authority_status: str
    owner: str


@dataclass(frozen=True)
class ActionPermissionRecord:
    permission_id: str
    action_surface: str
    action_class: str
    authorization: str
    condition: str
    precedence: int


@dataclass(frozen=True)
class SecurityCoverageRecord:
    coverage_id: str
    dimension: str
    coverage_status: str
    evidence_refs: list[str]


@dataclass(frozen=True)
class SecurityGovernanceErrorRecord:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class SecurityIntegrityScorecard:
    artifact_type: str
    artifact_id: str
    dimensions: dict[str, str]
    evidence: dict[str, list[str]]
    blockers: list[str]
    scorecard_hash: str
