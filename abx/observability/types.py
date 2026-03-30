from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ObservabilityCoverageRecord:
    coverage_id: str
    surface_ref: str
    coverage_state: str
    measurement_mode: str


@dataclass(frozen=True)
class BlindSpotRecord:
    blind_spot_id: str
    surface_ref: str
    blind_spot_state: str
    risk_level: str


@dataclass(frozen=True)
class MeasurementSufficiencyRecord:
    sufficiency_id: str
    surface_ref: str
    sufficiency_state: str
    consequence_class: str


@dataclass(frozen=True)
class InstrumentationFreshnessRecord:
    freshness_id: str
    surface_ref: str
    freshness_state: str
    freshness_reason: str


@dataclass(frozen=True)
class FalseAssuranceRecord:
    assurance_id: str
    surface_ref: str
    assurance_state: str
    assurance_reason: str


@dataclass(frozen=True)
class ObservabilityTransitionRecord:
    transition_id: str
    surface_ref: str
    from_state: str
    to_state: str
    reason: str


@dataclass(frozen=True)
class CoverageGovernanceErrorRecord:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class ObservabilityGovernanceScorecard:
    artifact_type: str
    artifact_id: str
    dimensions: dict[str, str]
    evidence: dict[str, list[str]]
    blockers: list[str]
    category: str
    scorecard_hash: str


@dataclass(frozen=True)
class ExplanationCoverageRecord:
    surface_id: str
    coverage_status: str
    owner: str


@dataclass(frozen=True)
class ExplainIRArtifact:
    artifact_id: str
    explain_rune_id: str
    event_type: str
    observed: list[str]
    inferred: list[str]
    speculative: list[str]
    confidence: float


@dataclass(frozen=True)
class ProvenancePartitionRecord:
    artifact_id: str
    observed_count: int
    inferred_count: int
    speculative_count: int


@dataclass(frozen=True)
class ObservabilitySurfaceRecord:
    surface_id: str
    source: str
    category: str
    state: str
    explain_enabled: bool


@dataclass(frozen=True)
class ObservabilityErrorRecord:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class ObservabilityHealthScorecard:
    artifact_type: str
    artifact_id: str
    dimensions: dict[str, str]
    evidence: dict[str, list[str]]
    blockers: list[str]
    scorecard_hash: str


@dataclass(frozen=True)
class CausalTraceRecord:
    trace_id: str
    run_id: str
    step: str
    relation: str
    evidence_ref: str
    state: str


@dataclass(frozen=True)
class TraceCoverageRecord:
    run_id: str
    traceable_surfaces: list[str]
    missing_surfaces: list[str]


@dataclass(frozen=True)
class CausalTraceSummary:
    artifact_id: str
    run_id: str
    steps: list[str]
    degraded_points: list[str]
    summary_hash: str


@dataclass(frozen=True)
class OperatorInsightView:
    view_id: str
    run_id: str
    overview: dict[str, object]
    drilldown: dict[str, object]
    view_hash: str
