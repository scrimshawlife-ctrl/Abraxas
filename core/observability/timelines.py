"""RuntimeTimelinePacket.v1

Deterministic ordered timeline of runtime events for an execution run.
Events are sorted by sequence number for determinism.
"""
from __future__ import annotations

import hashlib
import json
from typing import List, Optional

from core.models.governance import Authority


_SCHEMA_VERSION = "RuntimeTimelinePacket.v1"


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class RuntimeTimelineEvent:
    """A single event in the runtime timeline.

    Fields
    ------
    sequence     Integer sequence number (determines sort order)
    event_type   Type label (e.g. "node_executed", "node_blocked", "receipt_chained")
    source_hash  SHA-256 of the source artifact generating this event
    status       "completed" | "blocked" | "failed" | "skipped"
    """

    VALID_STATUSES = frozenset({"completed", "blocked", "failed", "skipped"})

    def __init__(
        self,
        *,
        sequence: int,
        event_type: str,
        source_hash: str,
        status: str,
    ) -> None:
        if sequence < 0:
            raise ValueError("sequence must be non-negative")
        if not event_type:
            raise ValueError("event_type must not be empty")
        if not source_hash:
            raise ValueError("source_hash must not be empty")
        if status not in self.VALID_STATUSES:
            raise ValueError(
                f"status must be one of {sorted(self.VALID_STATUSES)}, got {status!r}"
            )
        self.sequence = sequence
        self.event_type = event_type
        self.source_hash = source_hash
        self.status = status

    def to_dict(self) -> dict:
        return {
            "sequence": self.sequence,
            "event_type": self.event_type,
            "source_hash": self.source_hash,
            "status": self.status,
        }


def _compute_timeline_hash(events: List[RuntimeTimelineEvent]) -> str:
    sorted_events = sorted(events, key=lambda e: (e.sequence, e.source_hash))
    return _sha256(_canonical([e.to_dict() for e in sorted_events]))


class RuntimeTimelinePacket:
    """Deterministic runtime event timeline for an execution run.

    Fields
    ------
    schema_version  Fixed at "RuntimeTimelinePacket.v1"
    timeline_id     Unique identifier for this timeline
    execution_hash  Hash of the execution run
    events          List of RuntimeTimelineEvent, sorted by sequence
    timeline_hash   Deterministic hash over sorted events
    authority       Locked Authority token
    status          "valid" | "empty" | "sequence_conflict" | "failed"
    """

    schema_version: str = _SCHEMA_VERSION

    def __init__(
        self,
        *,
        timeline_id: str,
        execution_hash: str,
        events: List[RuntimeTimelineEvent],
        authority: Authority,
        status: Optional[str] = None,
    ) -> None:
        if not authority.is_locked():
            raise ValueError("authority must be locked")
        if not timeline_id:
            raise ValueError("timeline_id must not be empty")
        if not execution_hash:
            raise ValueError("execution_hash must not be empty")

        self.schema_version = _SCHEMA_VERSION
        self.timeline_id = timeline_id
        self.execution_hash = execution_hash
        # Sort deterministically by sequence then source_hash
        self.events = sorted(events, key=lambda e: (e.sequence, e.source_hash))
        self.authority = authority
        self.timeline_hash = _compute_timeline_hash(events)

        if status is not None:
            self.status = status
        elif not events:
            self.status = "empty"
        else:
            sequences = [e.sequence for e in events]
            if len(sequences) != len(set(sequences)):
                self.status = "sequence_conflict"
            else:
                self.status = "valid"

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "timeline_id": self.timeline_id,
            "execution_hash": self.execution_hash,
            "events": [e.to_dict() for e in self.events],
            "timeline_hash": self.timeline_hash,
            "authority": self.authority.to_dict(),
            "status": self.status,
        }


def build_runtime_timeline(
    *,
    timeline_id: str,
    execution_hash: str,
    events: List[RuntimeTimelineEvent],
    authority: Optional[Authority] = None,
) -> RuntimeTimelinePacket:
    """Factory for RuntimeTimelinePacket."""
    if authority is None:
        authority = Authority.locked()
    return RuntimeTimelinePacket(
        timeline_id=timeline_id,
        execution_hash=execution_hash,
        events=events,
        authority=authority,
    )
