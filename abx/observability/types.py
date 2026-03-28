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
