from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProductSurfaceRecord:
    surface_id: str
    capability: str
    audience: str
    surface_class: str
    contract_ref: str
    owner: str


@dataclass(frozen=True)
class PackagingContractRecord:
    contract_id: str
    package_name: str
    package_class: str
    compatibility: str
    boundedness: str
    capability_refs: list[str]


@dataclass(frozen=True)
class AudienceLegibilityRecord:
    audience_id: str
    audience_name: str
    entrypoint: str
    legibility_state: str
    expectation_surface: str


@dataclass(frozen=True)
class ProductBoundednessRecord:
    boundedness_id: str
    output_surface: str
    audience_name: str
    boundedness_state: str
    caveat_ref: str


@dataclass(frozen=True)
class OutputInterpretabilityRecord:
    interpretability_id: str
    output_surface: str
    audience_name: str
    interpretability_state: str
    degradation_visibility: str


@dataclass(frozen=True)
class PackageTierRecord:
    tier_id: str
    package_name: str
    tier_name: str
    semantics_scope: str
    restrictions: list[str]


@dataclass(frozen=True)
class ExternalConsumptionCoverageRecord:
    coverage_id: str
    dimension: str
    status: str
    evidence_refs: list[str]


@dataclass(frozen=True)
class ProductizationGovernanceErrorRecord:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class ProductizationGovernanceScorecard:
    artifact_type: str
    artifact_id: str
    dimensions: dict[str, str]
    evidence: dict[str, list[str]]
    blockers: list[str]
    scorecard_hash: str


@dataclass(frozen=True)
class AudienceEntrypointRecord:
    entrypoint_id: str
    audience_name: str
    start_surface: str
    drilldown_surfaces: list[str]
