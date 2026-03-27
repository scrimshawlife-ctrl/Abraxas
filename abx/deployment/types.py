from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DeploymentContractRecord:
    deployment_id: str
    entrypoint: str
    environment: str
    classification: str
    owner: str
    expected_inputs: list[str]
    expected_topology: str
    postconditions: list[str]


@dataclass(frozen=True)
class EnvironmentParityRecord:
    environment: str
    baseline_environment: str
    parity_status: str
    differences: list[str]
    owner: str


@dataclass(frozen=True)
class RuntimeTopologyRecord:
    topology_id: str
    environment: str
    topology_class: str
    nodes: list[str]
    edges: list[str]


@dataclass(frozen=True)
class TopologyCapabilityRecord:
    topology_id: str
    capability_id: str
    status: str


@dataclass(frozen=True)
class ConfigClassificationRecord:
    config_key: str
    classification: str
    owner: str
    affects: list[str]


@dataclass(frozen=True)
class SecretBoundaryRecord:
    secret_id: str
    boundary: str
    source: str
    semantic_risk: str


@dataclass(frozen=True)
class EnvironmentOverrideRecord:
    override_id: str
    environment: str
    target_key: str
    precedence: int
    containment: str


@dataclass(frozen=True)
class DeploymentDriftRecord:
    drift_id: str
    category: str
    severity: str
    message: str


@dataclass(frozen=True)
class DeploymentGovernanceErrorRecord:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class DeploymentGovernanceScorecard:
    artifact_type: str
    artifact_id: str
    dimensions: dict[str, str]
    evidence: dict[str, list[str]]
    blockers: list[str]
    scorecard_hash: str
