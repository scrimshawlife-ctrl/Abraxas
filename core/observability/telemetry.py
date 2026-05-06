"""ExecutionTelemetryPacket.v1

Deterministic telemetry for a single execution run. Captures hashes of
all execution surfaces so the run can be replayed and verified later.

Authority is locked at construction. All counts must be non-negative.
A replay mismatch forces deterministic_match=False.
"""
from __future__ import annotations

import hashlib
import json
from typing import Optional

from core.models.governance import Authority


_SCHEMA_VERSION = "ExecutionTelemetryPacket.v1"


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _canonical(obj: dict) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class ExecutionTelemetryPacket:
    """Deterministic telemetry snapshot for one execution run.

    Fields
    ------
    schema_version       Fixed at "ExecutionTelemetryPacket.v1"
    telemetry_id         Unique identifier for this packet
    execution_run_hash   SHA-256 of the execution run inputs
    graph_hash           SHA-256 of the route graph used
    traversal_hash       SHA-256 of the traversal sequence
    scheduler_hash       SHA-256 of the scheduler state
    replay_hash          Optional: SHA-256 of a replay run for comparison
    receipt_chain_hash   SHA-256 of the receipt chain
    executed_node_count  Number of nodes that executed successfully (>= 0)
    blocked_node_count   Number of blocked nodes (>= 0)
    failed_node_count    Number of failed nodes (>= 0)
    deterministic_match  True only when replay matches original exactly
    authority            Locked Authority token
    status               "valid" | "replay_mismatch" | "hash_missing" | "failed"
    """

    schema_version: str = _SCHEMA_VERSION

    def __init__(
        self,
        *,
        telemetry_id: str,
        execution_run_hash: str,
        graph_hash: str,
        traversal_hash: str,
        scheduler_hash: str,
        receipt_chain_hash: str,
        executed_node_count: int,
        blocked_node_count: int,
        failed_node_count: int,
        authority: Authority,
        replay_hash: Optional[str] = None,
        deterministic_match: Optional[bool] = None,
        status: str = "valid",
    ) -> None:
        if not authority.is_locked():
            raise ValueError("authority must be locked")
        if executed_node_count < 0:
            raise ValueError("executed_node_count must be non-negative")
        if blocked_node_count < 0:
            raise ValueError("blocked_node_count must be non-negative")
        if failed_node_count < 0:
            raise ValueError("failed_node_count must be non-negative")
        for name, h in [
            ("execution_run_hash", execution_run_hash),
            ("graph_hash", graph_hash),
            ("traversal_hash", traversal_hash),
            ("scheduler_hash", scheduler_hash),
            ("receipt_chain_hash", receipt_chain_hash),
        ]:
            if not h:
                raise ValueError(f"{name} must not be empty")

        self.schema_version = _SCHEMA_VERSION
        self.telemetry_id = telemetry_id
        self.execution_run_hash = execution_run_hash
        self.graph_hash = graph_hash
        self.traversal_hash = traversal_hash
        self.scheduler_hash = scheduler_hash
        self.replay_hash = replay_hash
        self.receipt_chain_hash = receipt_chain_hash
        self.executed_node_count = executed_node_count
        self.blocked_node_count = blocked_node_count
        self.failed_node_count = failed_node_count
        self.authority = authority
        self.status = status

        # Replay mismatch: if replay_hash present and differs, force False
        if deterministic_match is not None:
            self.deterministic_match = bool(deterministic_match)
        elif replay_hash is not None:
            self.deterministic_match = replay_hash == execution_run_hash
        else:
            self.deterministic_match = True

        if replay_hash is not None and replay_hash != execution_run_hash:
            self.deterministic_match = False
            if self.status == "valid":
                self.status = "replay_mismatch"

    def packet_hash(self) -> str:
        """Deterministic hash of this packet's content."""
        payload = {
            "schema_version": self.schema_version,
            "telemetry_id": self.telemetry_id,
            "execution_run_hash": self.execution_run_hash,
            "graph_hash": self.graph_hash,
            "traversal_hash": self.traversal_hash,
            "scheduler_hash": self.scheduler_hash,
            "replay_hash": self.replay_hash,
            "receipt_chain_hash": self.receipt_chain_hash,
            "executed_node_count": self.executed_node_count,
            "blocked_node_count": self.blocked_node_count,
            "failed_node_count": self.failed_node_count,
            "deterministic_match": self.deterministic_match,
            "status": self.status,
        }
        return _sha256(_canonical(payload))

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "telemetry_id": self.telemetry_id,
            "execution_run_hash": self.execution_run_hash,
            "graph_hash": self.graph_hash,
            "traversal_hash": self.traversal_hash,
            "scheduler_hash": self.scheduler_hash,
            "replay_hash": self.replay_hash,
            "receipt_chain_hash": self.receipt_chain_hash,
            "executed_node_count": self.executed_node_count,
            "blocked_node_count": self.blocked_node_count,
            "failed_node_count": self.failed_node_count,
            "deterministic_match": self.deterministic_match,
            "authority": self.authority.to_dict(),
            "status": self.status,
            "packet_hash": self.packet_hash(),
        }


def build_telemetry_packet(
    *,
    telemetry_id: str,
    execution_run_hash: str,
    graph_hash: str,
    traversal_hash: str,
    scheduler_hash: str,
    receipt_chain_hash: str,
    executed_node_count: int,
    blocked_node_count: int,
    failed_node_count: int,
    authority: Optional[Authority] = None,
    replay_hash: Optional[str] = None,
    status: str = "valid",
) -> ExecutionTelemetryPacket:
    """Factory function for ExecutionTelemetryPacket."""
    if authority is None:
        authority = Authority.locked()
    return ExecutionTelemetryPacket(
        telemetry_id=telemetry_id,
        execution_run_hash=execution_run_hash,
        graph_hash=graph_hash,
        traversal_hash=traversal_hash,
        scheduler_hash=scheduler_hash,
        receipt_chain_hash=receipt_chain_hash,
        executed_node_count=executed_node_count,
        blocked_node_count=blocked_node_count,
        failed_node_count=failed_node_count,
        authority=authority,
        replay_hash=replay_hash,
        status=status,
    )
