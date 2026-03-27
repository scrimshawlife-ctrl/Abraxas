from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModuleInteropRecord:
    interop_id: str
    producer_module: str
    consumer_module: str
    classification: str
    handoff_contract: str


@dataclass(frozen=True)
class CrossSystemContractRecord:
    contract_id: str
    owner: str
    classification: str
    compatibility: str


@dataclass(frozen=True)
class FederatedSemanticAlignmentRecord:
    alignment_id: str
    domain: str
    status: str
    details: str


@dataclass(frozen=True)
class CapabilityRegistryRecord:
    capability_id: str
    owner: str
    contract_id: str
    handoff_id: str


@dataclass(frozen=True)
class CapabilityHandoffRecord:
    handoff_id: str
    expected_inputs: list[str]
    expected_outputs: list[str]
    trust_propagation: str
    lifecycle_propagation: str


@dataclass(frozen=True)
class CapabilityDependencyRecord:
    capability_id: str
    depends_on: list[str]


@dataclass(frozen=True)
class FederationMismatchRecord:
    mismatch_id: str
    category: str
    severity: str
    message: str


@dataclass(frozen=True)
class FederationCoverageRecord:
    dimension: str
    status: str


@dataclass(frozen=True)
class FederationGovernanceErrorRecord:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class FederationGovernanceScorecard:
    artifact_type: str
    artifact_id: str
    dimensions: dict[str, str]
    evidence: dict[str, list[str]]
    blockers: list[str]
    scorecard_hash: str
