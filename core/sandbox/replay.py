"""SandboxReplayPacket.v1 - Replay verification for sandbox branches.

Rules:
- authority locked
- replay mismatch invalidates stabilization
"""
from __future__ import annotations

from hashlib import sha256
from typing import Any, List
import json

from pydantic import BaseModel

from core.models.governance import Authority

VALID_STATUSES = {"matched", "mismatch", "failed", "pending"}


class SandboxReplayPacket(BaseModel):
    schema_version: str = "SandboxReplayPacket.v1"
    replay_id: str
    source_branch_hash: str
    replay_branch_hash: str
    deterministic_match: bool
    mismatched_mutations: List[str]
    authority: Authority
    status: str

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        if not self.authority.is_locked():
            raise ValueError("authority must be locked")
        # A replay mismatch invalidates stabilization - enforce consistency
        if self.mismatched_mutations:
            object.__setattr__(self, "deterministic_match", False)
        if self.status not in VALID_STATUSES:
            raise ValueError(f"status must be one of {VALID_STATUSES}")

    def replay_hash(self) -> str:
        canonical = json.dumps(
            {
                "replay_id": self.replay_id,
                "source_branch_hash": self.source_branch_hash,
                "replay_branch_hash": self.replay_branch_hash,
                "deterministic_match": self.deterministic_match,
                "mismatched_mutations": sorted(self.mismatched_mutations),
            },
            sort_keys=True,
        ).encode("utf-8")
        return sha256(canonical).hexdigest()


def run_sandbox_replay(
    source_branch_hash: str,
    replay_branch_hash: str,
    replay_id: str,
    authority: Authority,
) -> SandboxReplayPacket:
    """Execute a deterministic sandbox replay.

    Compares source_branch_hash and replay_branch_hash. If equal, the
    replay is deterministically matched. Mismatch invalidates stabilization.
    """
    deterministic_match = source_branch_hash == replay_branch_hash
    mismatched: List[str] = []
    if not deterministic_match:
        mismatched = [f"branch_hash_mismatch:{source_branch_hash[:8]}vs{replay_branch_hash[:8]}"]

    status = "matched" if deterministic_match else "mismatch"

    return SandboxReplayPacket(
        replay_id=replay_id,
        source_branch_hash=source_branch_hash,
        replay_branch_hash=replay_branch_hash,
        deterministic_match=deterministic_match,
        mismatched_mutations=mismatched,
        authority=authority,
        status=status,
    )
