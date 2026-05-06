"""LineageTracePacket.v1

Deterministic execution lineage tracing. Each node in the lineage has
a parent reference (except root nodes). The chain hash is deterministic
over the sorted node list.

Authority is locked. Cyclic lineage is rejected (fail-closed).
Missing parent references trigger a failed status (fail-closed).
"""
from __future__ import annotations

import hashlib
import json
from typing import List, Optional

from core.models.governance import Authority


_SCHEMA_VERSION = "LineageTracePacket.v1"


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class LineageTraceNode:
    """A single node in the lineage trace.

    Fields
    ------
    node_id      Unique identifier for this node
    node_type    Type label (e.g. "execution", "rune", "receipt")
    source_hash  SHA-256 of the source artifact this node represents
    parent_hash  SHA-256 of the parent node's source_hash (None for root)
    generation   Depth from root (0 = root)
    """

    def __init__(
        self,
        *,
        node_id: str,
        node_type: str,
        source_hash: str,
        generation: int,
        parent_hash: Optional[str] = None,
    ) -> None:
        if not node_id:
            raise ValueError("node_id must not be empty")
        if not source_hash:
            raise ValueError("source_hash must not be empty")
        if generation < 0:
            raise ValueError("generation must be non-negative")
        self.node_id = node_id
        self.node_type = node_type
        self.source_hash = source_hash
        self.parent_hash = parent_hash
        self.generation = generation

    def node_hash(self) -> str:
        payload = {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "source_hash": self.source_hash,
            "parent_hash": self.parent_hash,
            "generation": self.generation,
        }
        return _sha256(_canonical(payload))

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "source_hash": self.source_hash,
            "parent_hash": self.parent_hash,
            "generation": self.generation,
        }


def _compute_chain_hash(nodes: List[LineageTraceNode]) -> str:
    """Compute a deterministic hash over sorted lineage nodes."""
    sorted_nodes = sorted(nodes, key=lambda n: (n.generation, n.node_id))
    node_dicts = [n.to_dict() for n in sorted_nodes]
    return _sha256(_canonical(node_dicts))


def _detect_cycles(nodes: List[LineageTraceNode]) -> bool:
    """Return True if a cycle exists in the parent references."""
    hash_to_node = {n.source_hash: n for n in nodes}
    for start in nodes:
        visited: set = set()
        current: Optional[str] = start.source_hash
        while current is not None:
            if current in visited:
                return True
            visited.add(current)
            node = hash_to_node.get(current)
            if node is None:
                break
            current = node.parent_hash
    return False


def _validate_parents(nodes: List[LineageTraceNode]) -> Optional[str]:
    """Return error message if parent references are invalid, else None."""
    known_hashes = {n.source_hash for n in nodes}
    for node in nodes:
        if node.parent_hash is not None and node.parent_hash not in known_hashes:
            return f"missing parent {node.parent_hash!r} for node {node.node_id!r}"
    return None


class LineageTracePacket:
    """Deterministic lineage trace for an execution run.

    Fields
    ------
    schema_version         Fixed at "LineageTracePacket.v1"
    trace_id               Unique identifier for this trace
    execution_hash         Hash of the execution run this trace covers
    nodes                  Ordered list of LineageTraceNode
    lineage_depth          Max generation depth in the trace
    deterministic_chain_hash  SHA-256 over sorted nodes
    authority              Locked Authority token
    status                 "valid" | "cyclic_lineage" | "missing_parent" | "failed"
    """

    schema_version: str = _SCHEMA_VERSION

    def __init__(
        self,
        *,
        trace_id: str,
        execution_hash: str,
        nodes: List[LineageTraceNode],
        authority: Authority,
        status: Optional[str] = None,
    ) -> None:
        if not authority.is_locked():
            raise ValueError("authority must be locked")
        if not trace_id:
            raise ValueError("trace_id must not be empty")
        if not execution_hash:
            raise ValueError("execution_hash must not be empty")

        self.schema_version = _SCHEMA_VERSION
        self.trace_id = trace_id
        self.execution_hash = execution_hash
        self.nodes = list(nodes)
        self.authority = authority

        # Determine lineage_depth
        self.lineage_depth = max((n.generation for n in nodes), default=0)

        # Validate — fail closed on problems
        if status is not None:
            self.status = status
        else:
            if _detect_cycles(nodes):
                self.status = "cyclic_lineage"
            else:
                missing_msg = _validate_parents(nodes)
                if missing_msg:
                    self.status = "missing_parent"
                else:
                    self.status = "valid"

        self.deterministic_chain_hash = _compute_chain_hash(nodes)

    def is_valid(self) -> bool:
        return self.status == "valid"

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "trace_id": self.trace_id,
            "execution_hash": self.execution_hash,
            "nodes": [n.to_dict() for n in self.nodes],
            "lineage_depth": self.lineage_depth,
            "deterministic_chain_hash": self.deterministic_chain_hash,
            "authority": self.authority.to_dict(),
            "status": self.status,
        }


def build_lineage_trace(
    *,
    trace_id: str,
    execution_hash: str,
    nodes: List[LineageTraceNode],
    authority: Optional[Authority] = None,
) -> LineageTracePacket:
    """Factory for LineageTracePacket."""
    if authority is None:
        authority = Authority.locked()
    return LineageTracePacket(
        trace_id=trace_id,
        execution_hash=execution_hash,
        nodes=nodes,
        authority=authority,
    )
