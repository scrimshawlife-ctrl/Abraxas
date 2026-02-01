"""
PolicySnapshot.v0 (stub)

Read-only policy envelope used by FAMILIAR runtime and gates.
Deterministic defaults; no external coupling required in v0.1.x.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import hashlib
import json


def _stable_json(data: Dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def _hash_payload(payload: Dict[str, Any]) -> str:
    return hashlib.sha256(_stable_json(payload).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class PolicySnapshot:
    snapshot_id: str

    # Feature toggles (explicit, deterministic)
    invariance_enabled: bool = False
    invariance_runs_required: int = 12

    stabilization_enabled_default: bool = False
    stabilization_window_size_default: int = 0

    # Tier/mode allowlists (shape enforcement only)
    allowed_tiers: List[str] = field(default_factory=lambda: ["Psychonaut", "Academic", "Enterprise"])
    allowed_modes: List[str] = field(default_factory=lambda: ["Oracle", "Ritual", "Analyst"])

    # Placeholder for coupling / overlay policy references
    coupling_map_ref: Optional[str] = None

    meta: Dict[str, Any] = field(default_factory=dict)

    not_computable: bool = False
    missing_fields: List[str] = field(default_factory=list)

    def validate(self) -> None:
        if not self.snapshot_id:
            raise ValueError("snapshot_id must be non-empty")
        if self.invariance_runs_required <= 0:
            raise ValueError("invariance_runs_required must be > 0")
        if self.stabilization_window_size_default < 0:
            raise ValueError("stabilization_window_size_default must be >= 0")
        if not isinstance(self.allowed_tiers, list) or not self.allowed_tiers:
            raise ValueError("allowed_tiers must be a non-empty list")
        if not isinstance(self.allowed_modes, list) or not self.allowed_modes:
            raise ValueError("allowed_modes must be a non-empty list")
        if not isinstance(self.meta, dict):
            raise ValueError("meta must be a dict")
        if self.not_computable and not self.missing_fields:
            raise ValueError("not_computable=True requires missing_fields to be non-empty")

    def to_payload(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "invariance_enabled": self.invariance_enabled,
            "invariance_runs_required": self.invariance_runs_required,
            "stabilization_enabled_default": self.stabilization_enabled_default,
            "stabilization_window_size_default": self.stabilization_window_size_default,
            "allowed_tiers": list(self.allowed_tiers),
            "allowed_modes": list(self.allowed_modes),
            "coupling_map_ref": self.coupling_map_ref,
            "meta": self.meta,
            "not_computable": self.not_computable,
            "missing_fields": list(self.missing_fields),
        }

    def hash(self) -> str:
        self.validate()
        return _hash_payload(self.to_payload())
