"""AdaptiveBranchLineage.v1 - Deterministic branch lineage tracking.

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


class AdaptiveBranchNode(BaseModel):
    branch_hash: str
    parent_branch_hash: Optional[str] = None
    mutation_hash: Optional[str] = None
    generation: int

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        if self.generation < 0:
            raise ValueError("generation must be non-negative")


class AdaptiveBranchLineage(BaseModel):
    schema_version: str = "AdaptiveBranchLineage.v1"
    lineage_id: str
    lineage_depth: int
    branch_nodes: List[AdaptiveBranchNode]
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
                "branch_hash": n.branch_hash,
                "parent_branch_hash": n.parent_branch_hash,
                "mutation_hash": n.mutation_hash,
                "generation": n.generation,
            }
            for n in sorted(self.branch_nodes, key=lambda n: n.generation)
        ]
        canonical = json.dumps(
            {
                "lineage_id": self.lineage_id,
                "nodes": nodes_repr,
            },
            sort_keys=True,
        ).encode("utf-8")
        return sha256(canonical).hexdigest()


def detect_cycles(nodes: List[AdaptiveBranchNode]) -> bool:
    """Detect cycles in branch lineage. Returns True if cycle found (fail-closed)."""
    parent_map: Dict[str, Optional[str]] = {
        n.branch_hash: n.parent_branch_hash for n in nodes
    }
    for start_hash in parent_map:
        visited = set()
        current = start_hash
        while current is not None:
            if current in visited:
                return True  # Cycle detected
            visited.add(current)
            current = parent_map.get(current)
    return False


def validate_parent_references(nodes: List[AdaptiveBranchNode]) -> bool:
    """Validate that all parent_branch_hash references exist in nodes."""
    known_hashes = {n.branch_hash for n in nodes}
    for node in nodes:
        if node.parent_branch_hash is not None:
            if node.parent_branch_hash not in known_hashes:
                return False
    return True


def build_branch_lineage(
    lineage_id: str,
    branch_nodes: List[AdaptiveBranchNode],
    authority: Authority,
) -> AdaptiveBranchLineage:
    """Build a deterministic AdaptiveBranchLineage with cycle detection.

    If cycles are detected, the lineage is marked failed (fail-closed).
    """
    if not authority.is_locked():
        raise ValueError("authority must be locked")

    # Detect cycles - fail closed
    if detect_cycles(branch_nodes):
        lineage = AdaptiveBranchLineage(
            lineage_id=lineage_id,
            lineage_depth=len(branch_nodes),
            branch_nodes=branch_nodes,
            deterministic_lineage_hash="",
            authority=authority,
            status="cyclic",
        )
        h = lineage.compute_lineage_hash()
        object.__setattr__(lineage, "deterministic_lineage_hash", h)
        return lineage

    # Validate parent references
    if not validate_parent_references(branch_nodes):
        lineage = AdaptiveBranchLineage(
            lineage_id=lineage_id,
            lineage_depth=len(branch_nodes),
            branch_nodes=branch_nodes,
            deterministic_lineage_hash="",
            authority=authority,
            status="invalid",
        )
        h = lineage.compute_lineage_hash()
        object.__setattr__(lineage, "deterministic_lineage_hash", h)
        return lineage

    lineage = AdaptiveBranchLineage(
        lineage_id=lineage_id,
        lineage_depth=len(branch_nodes),
        branch_nodes=branch_nodes,
        deterministic_lineage_hash="",
        authority=authority,
        status="valid",
    )
    h = lineage.compute_lineage_hash()
    object.__setattr__(lineage, "deterministic_lineage_hash", h)
    return lineage
