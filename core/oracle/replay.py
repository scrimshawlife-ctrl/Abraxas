"""IntakeReplayPacket.v1 - Replay verification for oracle intake normalization.

Rules:
- authority locked
- mismatched normalization invalidates replay
"""
from __future__ import annotations

from hashlib import sha256
from typing import Any, List
import json

from pydantic import BaseModel

from core.models.governance import Authority

VALID_STATUSES = {"matched", "mismatch", "failed", "pending"}


class IntakeReplayPacket(BaseModel):
    schema_version: str = "IntakeReplayPacket.v1"
    replay_id: str
    source_intake_hash: str
    replay_intake_hash: str
    deterministic_match: bool
    mismatched_normalizations: List[str]
    authority: Authority
    status: str

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        if not self.authority.is_locked():
            raise ValueError("authority must be locked")
        # Mismatched normalization invalidates replay
        if self.mismatched_normalizations:
            object.__setattr__(self, "deterministic_match", False)
        if self.status not in VALID_STATUSES:
            raise ValueError(f"status must be one of {VALID_STATUSES}")

    def replay_hash(self) -> str:
        canonical = json.dumps(
            {
                "replay_id": self.replay_id,
                "source_intake_hash": self.source_intake_hash,
                "replay_intake_hash": self.replay_intake_hash,
                "deterministic_match": self.deterministic_match,
                "mismatched_normalizations": sorted(self.mismatched_normalizations),
            },
            sort_keys=True,
        ).encode("utf-8")
        return sha256(canonical).hexdigest()


def run_intake_replay(
    source_intake_hash: str,
    replay_intake_hash: str,
    replay_id: str,
    authority: Authority,
    source_normalization_hash: str = "",
    replay_normalization_hash: str = "",
) -> IntakeReplayPacket:
    """Execute a deterministic intake replay.

    Compares source and replay intake hashes. Also checks normalization hashes
    if provided. Any mismatch invalidates the replay.
    """
    mismatched: List[str] = []

    hash_match = source_intake_hash == replay_intake_hash
    if not hash_match:
        mismatched.append(
            f"intake_hash_mismatch:{source_intake_hash[:8]}vs{replay_intake_hash[:8]}"
        )

    if source_normalization_hash and replay_normalization_hash:
        if source_normalization_hash != replay_normalization_hash:
            mismatched.append(
                f"normalization_hash_mismatch:{source_normalization_hash[:8]}"
                f"vs{replay_normalization_hash[:8]}"
            )

    deterministic_match = len(mismatched) == 0
    status = "matched" if deterministic_match else "mismatch"

    return IntakeReplayPacket(
        replay_id=replay_id,
        source_intake_hash=source_intake_hash,
        replay_intake_hash=replay_intake_hash,
        deterministic_match=deterministic_match,
        mismatched_normalizations=mismatched,
        authority=authority,
        status=status,
    )
