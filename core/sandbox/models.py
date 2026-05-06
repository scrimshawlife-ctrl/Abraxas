"""AdaptiveSandboxBranch.v1 - Isolated sandbox branch model.

Rules:
- authority locked
- sandbox isolated from runtime state
- deterministic hash stable
- branch_generation monotonic
"""
from __future__ import annotations

from hashlib import sha256
from typing import Any, Dict, Optional
import json

from pydantic import BaseModel

from core.models.governance import Authority

VALID_STABILIZATION_STATES = {"unstable", "stabilizing", "stable", "failed"}
VALID_STATUSES = {"pending", "active", "closed", "failed"}


class AdaptiveSandboxBranch(BaseModel):
    schema_version: str = "AdaptiveSandboxBranch.v1"
    branch_id: str
    source_state_hash: str
    sandbox_state_hash: str
    branch_generation: int
    sandbox_scope: str
    deterministic_branch_hash: str
    authority: Authority
    stabilization_state: str
    status: str

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        if not self.authority.is_locked():
            raise ValueError("authority must be locked")
        if self.branch_generation < 0:
            raise ValueError("branch_generation must be non-negative (monotonic)")
        if self.stabilization_state not in VALID_STABILIZATION_STATES:
            raise ValueError(
                f"stabilization_state must be one of {VALID_STABILIZATION_STATES}"
            )
        if self.status not in VALID_STATUSES:
            raise ValueError(f"status must be one of {VALID_STATUSES}")

    def compute_branch_hash(self) -> str:
        canonical = json.dumps(
            {
                "branch_id": self.branch_id,
                "source_state_hash": self.source_state_hash,
                "sandbox_state_hash": self.sandbox_state_hash,
                "branch_generation": self.branch_generation,
                "sandbox_scope": self.sandbox_scope,
            },
            sort_keys=True,
        ).encode("utf-8")
        return sha256(canonical).hexdigest()


def build_sandbox_branch(
    branch_id: str,
    source_state_hash: str,
    sandbox_scope: str,
    branch_generation: int,
    authority: Authority,
) -> AdaptiveSandboxBranch:
    """Create a new isolated AdaptiveSandboxBranch.

    The sandbox_state_hash and deterministic_branch_hash are derived
    deterministically from inputs; the sandbox is isolated from runtime state.
    """
    sandbox_state_hash = sha256(
        json.dumps(
            {
                "source_state_hash": source_state_hash,
                "sandbox_scope": sandbox_scope,
                "branch_generation": branch_generation,
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()

    branch = AdaptiveSandboxBranch(
        branch_id=branch_id,
        source_state_hash=source_state_hash,
        sandbox_state_hash=sandbox_state_hash,
        branch_generation=branch_generation,
        sandbox_scope=sandbox_scope,
        deterministic_branch_hash="",
        authority=authority,
        stabilization_state="unstable",
        status="active",
    )
    # Compute and assign the deterministic hash
    h = branch.compute_branch_hash()
    object.__setattr__(branch, "deterministic_branch_hash", h)
    return branch
