"""IntakeStabilizationPacket.v1 - Stabilization tracking for oracle intake.

Allowed stabilization_state:
- unstable
- stabilizing
- stable
- conflicted
- failed

Rules:
- authority locked
- replay failures affect stability
- unresolved conflicts block stable state
"""
from __future__ import annotations

from hashlib import sha256
from typing import Any
import json

from pydantic import BaseModel

from core.models.governance import Authority

VALID_STABILIZATION_STATES = {"unstable", "stabilizing", "stable", "conflicted", "failed"}
VALID_STATUSES = {"pending", "complete", "failed"}

STABILIZATION_WINDOW_DEFAULT = 3


class IntakeStabilizationPacket(BaseModel):
    schema_version: str = "IntakeStabilizationPacket.v1"
    stabilization_id: str
    intake_hash: str
    replay_match_count: int
    replay_failure_count: int
    conflict_count: int
    stabilization_window: int
    stabilization_state: str
    authority: Authority
    status: str

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        if not self.authority.is_locked():
            raise ValueError("authority must be locked")
        if self.stabilization_state not in VALID_STABILIZATION_STATES:
            raise ValueError(
                f"stabilization_state must be one of {VALID_STABILIZATION_STATES}"
            )
        if self.status not in VALID_STATUSES:
            raise ValueError(f"status must be one of {VALID_STATUSES}")
        if self.replay_match_count < 0:
            raise ValueError("replay_match_count must be non-negative")
        if self.replay_failure_count < 0:
            raise ValueError("replay_failure_count must be non-negative")
        if self.conflict_count < 0:
            raise ValueError("conflict_count must be non-negative")
        if self.stabilization_window < 1:
            raise ValueError("stabilization_window must be at least 1")

    def stabilization_hash(self) -> str:
        canonical = json.dumps(
            {
                "stabilization_id": self.stabilization_id,
                "intake_hash": self.intake_hash,
                "replay_match_count": self.replay_match_count,
                "replay_failure_count": self.replay_failure_count,
                "conflict_count": self.conflict_count,
                "stabilization_window": self.stabilization_window,
                "stabilization_state": self.stabilization_state,
            },
            sort_keys=True,
        ).encode("utf-8")
        return sha256(canonical).hexdigest()


def compute_intake_stabilization_state(
    replay_match_count: int,
    replay_failure_count: int,
    conflict_count: int,
    stabilization_window: int,
) -> str:
    """Deterministically compute intake stabilization state.

    Rules:
    - Unresolved conflicts block stable state => conflicted
    - Any failure => unstable or failed based on ratio
    - Matches >= window with zero failures and zero conflicts => stable
    - Matches > 0 with zero failures/conflicts but below window => stabilizing
    - Otherwise => unstable
    """
    # Unresolved conflicts block stable state
    if conflict_count > 0:
        return "conflicted"
    if replay_failure_count > 0:
        if replay_match_count == 0:
            return "failed"
        return "unstable"
    if replay_match_count >= stabilization_window:
        return "stable"
    if replay_match_count > 0:
        return "stabilizing"
    return "unstable"


def build_intake_stabilization_packet(
    stabilization_id: str,
    intake_hash: str,
    replay_match_count: int,
    replay_failure_count: int,
    conflict_count: int,
    authority: Authority,
    stabilization_window: int = STABILIZATION_WINDOW_DEFAULT,
) -> IntakeStabilizationPacket:
    """Build a deterministic IntakeStabilizationPacket."""
    state = compute_intake_stabilization_state(
        replay_match_count, replay_failure_count, conflict_count, stabilization_window
    )
    status = "complete" if state in {"stable", "stabilizing"} else (
        "failed" if state in {"failed"} else "pending"
    )
    return IntakeStabilizationPacket(
        stabilization_id=stabilization_id,
        intake_hash=intake_hash,
        replay_match_count=replay_match_count,
        replay_failure_count=replay_failure_count,
        conflict_count=conflict_count,
        stabilization_window=stabilization_window,
        stabilization_state=state,
        authority=authority,
        status=status,
    )
