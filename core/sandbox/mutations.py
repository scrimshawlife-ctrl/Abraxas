"""CandidateMutationPacket.v1 - Governed mutation proposals in sandbox.

Allowed mutation_type:
- route_adjustment
- validation_adjustment
- replay_adjustment
- stabilization_adjustment
- projection_adjustment
- topology_adjustment

Rules:
- authority locked
- mutation isolated to sandbox
- deterministic hash stable
"""
from __future__ import annotations

from hashlib import sha256
from typing import Any, Dict, List
import json

from pydantic import BaseModel

from core.models.governance import Authority

ALLOWED_MUTATION_TYPES = {
    "route_adjustment",
    "validation_adjustment",
    "replay_adjustment",
    "stabilization_adjustment",
    "projection_adjustment",
    "topology_adjustment",
}

VALID_STATUSES = {"proposed", "accepted", "rejected", "invalidated"}


class CandidateMutationPacket(BaseModel):
    schema_version: str = "CandidateMutationPacket.v1"
    mutation_id: str
    source_branch_hash: str
    target_branch_hash: str
    mutation_type: str
    proposed_transition_hashes: List[str]
    deterministic_mutation_hash: str
    authority: Authority
    requires_operator_review: bool
    status: str

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        if not self.authority.is_locked():
            raise ValueError("authority must be locked")
        if self.mutation_type not in ALLOWED_MUTATION_TYPES:
            raise ValueError(
                f"mutation_type must be one of {sorted(ALLOWED_MUTATION_TYPES)}"
            )
        if self.status not in VALID_STATUSES:
            raise ValueError(f"status must be one of {VALID_STATUSES}")

    def compute_mutation_hash(self) -> str:
        canonical = json.dumps(
            {
                "mutation_id": self.mutation_id,
                "source_branch_hash": self.source_branch_hash,
                "target_branch_hash": self.target_branch_hash,
                "mutation_type": self.mutation_type,
                "proposed_transition_hashes": sorted(self.proposed_transition_hashes),
            },
            sort_keys=True,
        ).encode("utf-8")
        return sha256(canonical).hexdigest()


def build_mutation_packet(
    mutation_id: str,
    source_branch_hash: str,
    target_branch_hash: str,
    mutation_type: str,
    proposed_transition_hashes: List[str],
    authority: Authority,
    requires_operator_review: bool = True,
) -> CandidateMutationPacket:
    """Create an isolated CandidateMutationPacket with deterministic hash."""
    if mutation_type not in ALLOWED_MUTATION_TYPES:
        raise ValueError(
            f"mutation_type must be one of {sorted(ALLOWED_MUTATION_TYPES)}"
        )

    packet = CandidateMutationPacket(
        mutation_id=mutation_id,
        source_branch_hash=source_branch_hash,
        target_branch_hash=target_branch_hash,
        mutation_type=mutation_type,
        proposed_transition_hashes=sorted(proposed_transition_hashes),
        deterministic_mutation_hash="",
        authority=authority,
        requires_operator_review=requires_operator_review,
        status="proposed",
    )
    h = packet.compute_mutation_hash()
    object.__setattr__(packet, "deterministic_mutation_hash", h)
    return packet
