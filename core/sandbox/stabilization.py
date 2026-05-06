"""SandboxStabilizationPacket.v1 - Stabilization tracking for sandbox branches.

Allowed stabilization_state:
- unstable
- stabilizing
- stable
- failed

Rules:
- authority locked
- replay failures affect stability
- deterministic stabilization semantics
"""
from __future__ import annotations

from hashlib import sha256
from typing import Any
import json

from pydantic import BaseModel

from core.models.governance import Authority

VALID_STABILIZATION_STATES = {"unstable", "stabilizing", "stable", "failed"}
VALID_STATUSES = {"pending", "complete", "failed"}

STABILIZATION_WINDOW_DEFAULT = 3


class SandboxStabilizationPacket(BaseModel):
    schema_version: str = "SandboxStabilizationPacket.v1"
    stabilization_id: str
    sandbox_branch_hash: str
    replay_match_count: int
    replay_failure_count: int
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
        if self.stabilization_window < 1:
            raise ValueError("stabilization_window must be at least 1")

    def stabilization_hash(self) -> str:
        canonical = json.dumps(
            {
                "stabilization_id": self.stabilization_id,
                "sandbox_branch_hash": self.sandbox_branch_hash,
                "replay_match_count": self.replay_match_count,
                "replay_failure_count": self.replay_failure_count,
                "stabilization_window": self.stabilization_window,
                "stabilization_state": self.stabilization_state,
            },
            sort_keys=True,
        ).encode("utf-8")
        return sha256(canonical).hexdigest()


def compute_stabilization_state(
    replay_match_count: int,
    replay_failure_count: int,
    stabilization_window: int,
) -> str:
    """Deterministically compute stabilization state from replay counts.

    Rules:
    - Any failure -> unstable or failed based on ratio
    - Matches >= window with zero failures -> stable
    - Matches > 0 with zero failures but below window -> stabilizing
    - Otherwise -> unstable
    """
    if replay_failure_count > 0:
        if replay_match_count == 0:
            return "failed"
        # More failures than matches -> unstable
        if replay_failure_count >= replay_match_count:
            return "unstable"
        return "unstable"
    if replay_match_count >= stabilization_window:
        return "stable"
    if replay_match_count > 0:
        return "stabilizing"
    return "unstable"


def build_stabilization_packet(
    stabilization_id: str,
    sandbox_branch_hash: str,
    replay_match_count: int,
    replay_failure_count: int,
    authority: Authority,
    stabilization_window: int = STABILIZATION_WINDOW_DEFAULT,
) -> SandboxStabilizationPacket:
    """Build a deterministic SandboxStabilizationPacket."""
    state = compute_stabilization_state(
        replay_match_count, replay_failure_count, stabilization_window
    )
    status = "complete" if state in {"stable", "stabilizing"} else (
        "failed" if state == "failed" else "pending"
    )
    return SandboxStabilizationPacket(
        stabilization_id=stabilization_id,
        sandbox_branch_hash=sandbox_branch_hash,
        replay_match_count=replay_match_count,
        replay_failure_count=replay_failure_count,
        stabilization_window=stabilization_window,
        stabilization_state=state,
        authority=authority,
        status=status,
    )
