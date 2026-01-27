"""
TaskGraphIR.v0

Deterministic, hashable representation of an operator request
decomposed into executable operations with explicit constraints.

This IR contains NO inference logic.
It encodes intent, scope, and limits only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import hashlib
import json


# -------------------------
# Canonical Enums (v0)
# -------------------------

TIER_SCOPES = {"Psychonaut", "Academic", "Enterprise"}
MODES = {"Oracle", "Ritual", "Analyst"}


# -------------------------
# Helpers
# -------------------------

def _stable_json(data: Dict[str, Any]) -> str:
    """
    Produce a stable JSON string for hashing.
    Sorting and separators are fixed to guarantee determinism.
    """
    return json.dumps(
        data,
        sort_keys=True,
        ensure_ascii=True,
        separators=(",", ":"),
    )


def _hash_payload(payload: Dict[str, Any]) -> str:
    """
    Canonical hash function for TaskGraphIR.
    """
    stable = _stable_json(payload)
    return hashlib.sha256(stable.encode("utf-8")).hexdigest()


# -------------------------
# IR Definition
# -------------------------

@dataclass(frozen=True)
class TaskGraphIR:
    """
    TaskGraphIR.v0

    Rules:
    - All fields must be explicit.
    - Unknown values MUST be None and explicitly flagged.
    - No derived or inferred fields are permitted.
    """

    task_id: str

    tier_scope: str
    mode: str

    requested_ops: List[str]

    constraints: Dict[str, Any]

    assumptions: List[str] = field(default_factory=list)

    # Explicit flags
    not_computable: bool = False
    missing_fields: List[str] = field(default_factory=list)

    # -------------------------
    # Validation
    # -------------------------

    def validate(self) -> None:
        """
        Validate schema-level invariants.
        Raises ValueError on violation.
        """
        if self.tier_scope not in TIER_SCOPES:
            raise ValueError(f"Invalid tier_scope: {self.tier_scope}")

        if self.mode not in MODES:
            raise ValueError(f"Invalid mode: {self.mode}")

        if not isinstance(self.requested_ops, list):
            raise ValueError("requested_ops must be a list")

        if not isinstance(self.constraints, dict):
            raise ValueError("constraints must be a dict")

        if not isinstance(self.assumptions, list):
            raise ValueError("assumptions must be a list")

        if self.not_computable and not self.missing_fields:
            raise ValueError(
                "not_computable=True requires missing_fields to be non-empty"
            )

    # -------------------------
    # Hashing
    # -------------------------

    def to_payload(self) -> Dict[str, Any]:
        """
        Convert to a canonical payload for hashing and comparison.
        """
        return {
            "task_id": self.task_id,
            "tier_scope": self.tier_scope,
            "mode": self.mode,
            "requested_ops": list(self.requested_ops),
            "constraints": self.constraints,
            "assumptions": list(self.assumptions),
            "not_computable": self.not_computable,
            "missing_fields": list(self.missing_fields),
        }

    def hash(self) -> str:
        """
        Return the canonical SHA-256 hash of this TaskGraphIR.
        """
        self.validate()
        return _hash_payload(self.to_payload())

    # -------------------------
    # Deterministic Equality
    # -------------------------

    def semantically_equal(self, other: "TaskGraphIR") -> bool:
        """
        Semantic equality is strict hash equality.
        """
        if not isinstance(other, TaskGraphIR):
            return False
        return self.hash() == other.hash()
