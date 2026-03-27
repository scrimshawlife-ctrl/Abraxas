from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DocumentationSurfaceRecord:
    doc_id: str
    path: str
    doc_class: str
    canonical_linkage: str
    ownership: str


@dataclass(frozen=True)
class HandoffRecord:
    handoff_id: str
    role_from: str
    role_to: str
    packet_class: str
    completeness: str
    risk_state: str


@dataclass(frozen=True)
class RoleLegibilityRecord:
    role_id: str
    role_name: str
    entry_surface: str
    coverage_state: str
    ownership_scope: str


@dataclass(frozen=True)
class DocumentationFreshnessRecord:
    freshness_id: str
    doc_id: str
    freshness_state: str
    refresh_mode: str
    owner: str


@dataclass(frozen=True)
class RefreshDependencyRecord:
    dependency_id: str
    doc_id: str
    depends_on: str
    dependency_class: str


@dataclass(frozen=True)
class KnowledgeTransferCoverageRecord:
    coverage_id: str
    dimension: str
    status: str
    evidence_refs: list[str]


@dataclass(frozen=True)
class DocumentationGovernanceErrorRecord:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class DocumentationLegibilityScorecard:
    artifact_type: str
    artifact_id: str
    dimensions: dict[str, str]
    evidence: dict[str, list[str]]
    blockers: list[str]
    scorecard_hash: str


@dataclass(frozen=True)
class OnboardingEntryRecord:
    entry_id: str
    role_name: str
    first_surfaces: list[str]
    sequence_class: str


@dataclass(frozen=True)
class RoleEntrypointRecord:
    entrypoint_id: str
    role_name: str
    overview_surface: str
    drilldown_surfaces: list[str]
