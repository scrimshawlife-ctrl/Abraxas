"""IntakeLineagePacket.v1 - Deterministic lineage tracking for oracle intake.

Rules:
- lineage deterministic
- cyclic lineage fail closed
- parent references valid
"""
from __future__ import annotations

from hashlib import sha256
from typing import Any, Dict, List, Optional
import json

from pydantic import BaseModel

from core.models.governance import Authority

VALID_STATUSES = {"valid", "cyclic", "invalid", "failed"}


class IntakeLineageNode(BaseModel):
    intake_hash: str
    parent_hash: Optional[str] = None
    generation: int
    normalization_hash: Optional[str] = None

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        if self.generation < 0:
            raise ValueError("generation must be non-negative")


class IntakeLineagePacket(BaseModel):
    schema_version: str = "IntakeLineagePacket.v1"
    lineage_id: str
    lineage_depth: int
    lineage_nodes: List[IntakeLineageNode]
    deterministic_lineage_hash: str
    authority: Authority
    status: str

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        if not self.authority.is_locked():
            raise ValueError("authority must be locked")
        if self.status not in VALID_STATUSES:
            raise ValueError(f"status must be one of {VALID_STATUSES}")

    def compute_lineage_hash(self) -> str:
        nodes_repr = [
            {
                "intake_hash": n.intake_hash,
                "parent_hash": n.parent_hash,
                "generation": n.generation,
                "normalization_hash": n.normalization_hash,
            }
            for n in sorted(self.lineage_nodes, key=lambda n: n.generation)
        ]
        canonical = json.dumps(
            {
                "lineage_id": self.lineage_id,
                "nodes": nodes_repr,
            },
            sort_keys=True,
        ).encode("utf-8")
        return sha256(canonical).hexdigest()


def detect_lineage_cycles(nodes: List[IntakeLineageNode]) -> bool:
    """Detect cycles in intake lineage. Returns True if cycle found (fail-closed)."""
    parent_map: Dict[str, Optional[str]] = {
        n.intake_hash: n.parent_hash for n in nodes
    }
    for start_hash in parent_map:
        visited: set[str] = set()
        current: Optional[str] = start_hash
        while current is not None:
            if current in visited:
                return True  # Cycle detected
            visited.add(current)
            current = parent_map.get(current)
    return False


def validate_lineage_parent_references(nodes: List[IntakeLineageNode]) -> bool:
    """Validate that all parent_hash references exist in nodes."""
    known_hashes = {n.intake_hash for n in nodes}
    for node in nodes:
        if node.parent_hash is not None:
            if node.parent_hash not in known_hashes:
                return False
    return True


def build_intake_lineage(
    lineage_id: str,
    lineage_nodes: List[IntakeLineageNode],
    authority: Authority,
) -> IntakeLineagePacket:
    """Build a deterministic IntakeLineagePacket with cycle detection.

    Cyclic lineage fails closed (status=cyclic).
    Invalid parent references fail as invalid.
    """
    if not authority.is_locked():
        raise ValueError("authority must be locked")

    # Detect cycles - fail closed
    if detect_lineage_cycles(lineage_nodes):
        lineage = IntakeLineagePacket(
            lineage_id=lineage_id,
            lineage_depth=len(lineage_nodes),
            lineage_nodes=lineage_nodes,
            deterministic_lineage_hash="",
            authority=authority,
            status="cyclic",
        )
        h = lineage.compute_lineage_hash()
        object.__setattr__(lineage, "deterministic_lineage_hash", h)
        return lineage

    # Validate parent references
    if not validate_lineage_parent_references(lineage_nodes):
        lineage = IntakeLineagePacket(
            lineage_id=lineage_id,
            lineage_depth=len(lineage_nodes),
            lineage_nodes=lineage_nodes,
            deterministic_lineage_hash="",
            authority=authority,
            status="invalid",
        )
        h = lineage.compute_lineage_hash()
        object.__setattr__(lineage, "deterministic_lineage_hash", h)
        return lineage

    lineage = IntakeLineagePacket(
        lineage_id=lineage_id,
        lineage_depth=len(lineage_nodes),
        lineage_nodes=lineage_nodes,
        deterministic_lineage_hash="",
        authority=authority,
        status="valid",
    )
    h = lineage.compute_lineage_hash()
    object.__setattr__(lineage, "deterministic_lineage_hash", h)
    return lineage
