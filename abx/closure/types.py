from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ClosureSurfaceRecord:
    surface_id: str
    domain_id: str
    upstream_artifact: str
    dependency_ids: list[str]
    waiver_ids: list[str]


@dataclass(frozen=True)
class ClosureDependencyRecord:
    dependency_id: str
    domain_id: str
    depends_on: list[str]


@dataclass(frozen=True)
class SystemClosureRecord:
    record_id: str
    closure_state: str
    domain_states: dict[str, str]
    dependency_states: dict[str, str]
    waived_domains: list[str]
    blocked_domains: list[str]
    degraded_domains: list[str]
    partial_domains: list[str]
    evidence_refs: list[str]


@dataclass(frozen=True)
class AuditSurfaceRecord:
    surface_id: str
    bundle_scope: str
    required_domains: list[str]
    optional_domains: list[str]


@dataclass(frozen=True)
class EvidenceBundleRecord:
    bundle_id: str
    scope: str
    included_evidence: list[str]
    missing_required_domains: list[str]
    stale_evidence_refs: list[str]
    blocked_domains: list[str]


@dataclass(frozen=True)
class AuditReadinessRecord:
    record_id: str
    readiness_state: str
    bundle_states: dict[str, str]
    blocked_bundles: list[str]
    stale_bundles: list[str]
    incomplete_bundles: list[str]
    evidence_refs: list[str]


@dataclass(frozen=True)
class RatificationCriteriaRecord:
    criteria_id: str
    scope: str
    required_domains: list[str]
    requires_audit_ready: bool
    max_waived_domains: int


@dataclass(frozen=True)
class RatificationDecisionRecord:
    decision_id: str
    scope: str
    decision_state: str
    satisfied_criteria: list[str]
    unmet_criteria: list[str]
    waived_criteria: list[str]
    evidence_bundle_ids: list[str]


@dataclass(frozen=True)
class ResidualGapRecord:
    gap_id: str
    domain_id: str
    classification: str
    severity: str
    evidence_ref: str


@dataclass(frozen=True)
class NonClosureRecord:
    non_closure_id: str
    classification: str
    domain_id: str
    reason: str
    evidence_ref: str


@dataclass(frozen=True)
class ExceptionAggregationRecord:
    aggregation_id: str
    totals_by_classification: dict[str, int]
    blocking_domains: list[str]
    stale_exceptions: list[str]


@dataclass(frozen=True)
class ClosureGovernanceErrorRecord:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class ClosureRatificationScorecard:
    artifact_type: str
    artifact_id: str
    dimensions: dict[str, str]
    evidence: dict[str, list[str]]
    blockers: list[str]
    category: str
    scorecard_hash: str
