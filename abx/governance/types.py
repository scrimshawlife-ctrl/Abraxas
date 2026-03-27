from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CanonicalSchemaRecord:
    schema_id: str
    module_path: str
    artifact_type: str
    classification: str
    authority_level: str
    notes: str


@dataclass(frozen=True)
class SchemaMappingRecord:
    mapping_id: str
    canonical_schema_id: str
    alias_surface: str
    field_mappings: list[tuple[str, str]]
    status: str


@dataclass(frozen=True)
class LegacySurfaceRecord:
    surface_id: str
    surface_path: str
    reason: str
    status: str


@dataclass(frozen=True)
class DeadPathRecord:
    path: str
    path_type: str
    evidence: str
    confidence: str


@dataclass(frozen=True)
class SourceOfTruthRecord:
    domain: str
    authoritative_surface: str
    derived_surfaces: list[str]
    adapted_surfaces: list[str]
    deprecated_surfaces: list[str]


@dataclass(frozen=True)
class CanonicalManifestArtifact:
    artifact_type: str
    artifact_id: str
    baseline_id: str
    baseline_version: str
    members: list[dict[str, str]]
    exclusions: list[str]
    manifest_hash: str


@dataclass(frozen=True)
class MigrationGuardResult:
    artifact_type: str
    artifact_id: str
    baseline_id: str
    status: str
    compatible_additive: list[str]
    migration_required: list[str]
    breaking: list[str]
    not_computable: list[str]
    guard_hash: str


@dataclass(frozen=True)
class BreakingChangeReport:
    artifact_type: str
    artifact_id: str
    baseline_id: str
    status: str
    additive_changes: list[str]
    breaking_changes: list[str]
    migration_required_changes: list[str]
    heuristic_warnings: list[str]
    report_hash: str


@dataclass(frozen=True)
class RepoHealthScorecard:
    artifact_type: str
    artifact_id: str
    baseline_id: str
    overall_status: str
    component_scores: dict[str, int]
    blockers: list[str]
    weak_zones: list[str]
    scorecard_hash: str


@dataclass(frozen=True)
class BaselineReleasePrepArtifact:
    artifact_type: str
    artifact_id: str
    baseline_id: str
    release_state: str
    blockers: list[str]
    evidence_refs: list[str]
    release_notes_scaffold: dict[str, Any]
    tag_metadata: dict[str, str]
    prep_hash: str


@dataclass(frozen=True)
class BaselineEnforcementResult:
    artifact_type: str
    artifact_id: str
    baseline_id: str
    status: str
    blocking_checks: list[str]
    warning_checks: list[str]
    informational_checks: list[str]
    waived_checks: list[str]
    enforcement_hash: str


@dataclass(frozen=True)
class ChangeControlRequestArtifact:
    artifact_type: str
    artifact_id: str
    request_id: str
    change_type: str
    affected_surfaces: list[str]
    required_evidence: list[str]
    waiver_required: bool
    risk_status: str
    request_hash: str


@dataclass(frozen=True)
class GovernedUpgradePlan:
    artifact_type: str
    artifact_id: str
    baseline_from: str
    baseline_to: str
    affected_surfaces: list[str]
    compatibility_status: str
    migration_bundle_refs: list[str]
    blockers: list[str]
    readiness_state: str
    plan_hash: str


@dataclass(frozen=True)
class WaiverRecord:
    waiver_id: str
    owner: str
    reason: str
    scope: list[str]
    status: str
    expires_on: str
    related_checks: list[str]


@dataclass(frozen=True)
class WaiverAuditArtifact:
    artifact_type: str
    artifact_id: str
    active_waivers: list[dict[str, Any]]
    expired_waivers: list[dict[str, Any]]
    invalid_waivers: list[dict[str, Any]]
    audit_hash: str


@dataclass(frozen=True)
class MaintenanceCycleArtifact:
    artifact_type: str
    artifact_id: str
    cycle_id: str
    cadence: str
    cycle_state: str
    checks_run: list[str]
    blockers: list[str]
    cycle_hash: str


@dataclass(frozen=True)
class MaintenanceSummaryArtifact:
    artifact_type: str
    artifact_id: str
    latest_cycle_id: str
    summary_state: str
    stale_waivers: list[str]
    drift_risks: list[str]
    upgrade_backlog: list[str]
    summary_hash: str


@dataclass(frozen=True)
class RepoAuditArtifact:
    artifact_type: str
    artifact_id: str
    generated_at: str
    schema_summary: dict[str, int]
    source_of_truth_summary: dict[str, int]
    pruning_summary: dict[str, int]
    coupling_summary: dict[str, Any]
    blockers: list[str]
    enforced_checks: list[str]
    reported_only_checks: list[str]
    audit_hash: str


@dataclass(frozen=True)
class ReleaseCandidateReadinessArtifact:
    artifact_type: str
    artifact_id: str
    status: str
    blockers: list[str]
    canonical_manifest: dict[str, str]
    staged_deprecations: list[str]
    recommendations: list[str]
    readiness_hash: str
