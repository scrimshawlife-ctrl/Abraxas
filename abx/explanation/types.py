from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NarrativeCompressionRecord:
    compression_id: str
    surface_ref: str
    compression_mode: str
    compression_state: str
    omitted_context: str


@dataclass(frozen=True)
class ExplanationBoundaryRecord:
    boundary_id: str
    surface_ref: str
    boundary_state: str
    boundary_reason: str


@dataclass(frozen=True)
class ExplanationLayerRecord:
    layer_id: str
    surface_ref: str
    layer_state: str
    evidence_ref: str


@dataclass(frozen=True)
class InterpretiveHonestyRecord:
    honesty_id: str
    surface_ref: str
    honesty_state: str
    smoothing_risk: str


@dataclass(frozen=True)
class CausalLanguageRecord:
    causal_id: str
    surface_ref: str
    causal_state: str
    support_state: str


@dataclass(frozen=True)
class OmissionRiskRecord:
    omission_id: str
    surface_ref: str
    omission_state: str
    caveat_required: str


@dataclass(frozen=True)
class ExplanationTransitionRecord:
    transition_id: str
    surface_ref: str
    from_state: str
    to_state: str
    reason: str
    trust_posture: str


@dataclass(frozen=True)
class CompressionLossRecord:
    loss_id: str
    surface_ref: str
    loss_state: str
    loss_scope: str


@dataclass(frozen=True)
class ExplanationGovernanceErrorRecord:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class ExplanationGovernanceScorecard:
    artifact_type: str
    artifact_id: str
    dimensions: dict[str, str]
    evidence: dict[str, list[str]]
    blockers: list[str]
    category: str
    scorecard_hash: str
