from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class InputEnvelope:
    envelope_id: str
    source: str
    interface_id: str
    payload: dict[str, Any]
    trust_state: str
    received_tick: int


@dataclass(frozen=True)
class NormalizedInput:
    normalized_id: str
    envelope_id: str
    normalized_payload: dict[str, Any]
    normalization_steps: list[str]


@dataclass(frozen=True)
class TrustClassificationRecord:
    envelope_id: str
    trust_state: str
    rationale: str


@dataclass(frozen=True)
class InterfaceContractRecord:
    interface_id: str
    version: str
    owner: str
    required_fields: list[str]
    optional_fields: list[str]
    exposure: str


@dataclass(frozen=True)
class AdapterTransformRecord:
    adapter_id: str
    connector_id: str
    transform_type: str
    input_trust: str
    output_trust: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class BoundaryErrorRecord:
    code: str
    severity: str
    category: str
    message: str


@dataclass(frozen=True)
class BoundaryValidationResult:
    envelope_id: str
    status: str
    state: str
    accepted: bool
    errors: list[BoundaryErrorRecord]


@dataclass(frozen=True)
class ProvenanceCarryRecord:
    envelope_id: str
    source: str
    trust_state: str
    carried_fields: list[str]


@dataclass(frozen=True)
class ConnectorCapabilityRecord:
    connector_id: str
    role: str
    allowed_actions: list[str]
    disallowed_actions: list[str]


@dataclass(frozen=True)
class BoundaryHealthScorecard:
    artifact_type: str
    artifact_id: str
    dimensions: dict[str, str]
    evidence: dict[str, list[str]]
    blockers: list[str]
    scorecard_hash: str
