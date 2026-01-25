from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class UpgradeCandidate:
    version: str
    run_id: str
    created_at: str
    input_hash: str
    candidate_id: str
    source_loop: str
    change_type: str
    target_paths: List[str]
    patch_plan: Dict[str, Any]
    evidence_refs: List[str]
    constraints: Dict[str, Any]
    not_computable: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GateReport:
    order: List[str]
    schema_validation: Dict[str, Any]
    dozen_run_invariance: Dict[str, Any]
    rent_enforcement: Dict[str, Any]
    missing_input: Dict[str, Any]
    overall_ok: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class UpgradeDecision:
    version: str
    run_id: str
    created_at: str
    input_hash: str
    candidate_id: str
    decision_id: str
    status: str
    reasons: List[str] = field(default_factory=list)
    gate_report: Optional[Dict[str, Any]] = None
    not_computable: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class UpgradeProvenanceBundle:
    version: str
    run_id: str
    created_at: str
    input_hash: str
    candidate_id: str
    decision_id: str
    environment: Dict[str, Any]
    artifact_paths: Dict[str, str]
    inputs_manifest: Dict[str, Any]
    artifact_dir: Optional[str] = None
    artifact_hashes: Optional[Dict[str, str]] = None
    gate_report: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
