"""SourceEvidencePacket.v1 - Typed evidence packets for oracle intake.

Rules:
- authority locked
- provenance_chain deterministic
- missing provenance => fail closed
"""
from __future__ import annotations

from hashlib import sha256
from typing import Any, List
import json

from pydantic import BaseModel

from core.models.governance import Authority

VALID_EVIDENCE_TYPES = {
    "structural",
    "execution",
    "replay",
    "topology",
    "stabilization",
    "projection",
    "sandbox",
}

VALID_STATUSES = {"valid", "invalid", "not_computable", "failed"}


class SourceEvidencePacket(BaseModel):
    schema_version: str = "SourceEvidencePacket.v1"
    evidence_id: str
    intake_hash: str
    source_hash: str
    provenance_chain: List[str]
    evidence_type: str
    authority: Authority
    status: str

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        if not self.authority.is_locked():
            raise ValueError("authority must be locked")
        if self.evidence_type not in VALID_EVIDENCE_TYPES:
            raise ValueError(f"evidence_type must be one of {VALID_EVIDENCE_TYPES}")
        if self.status not in VALID_STATUSES:
            raise ValueError(f"status must be one of {VALID_STATUSES}")

    def evidence_hash(self) -> str:
        canonical = json.dumps(
            {
                "evidence_id": self.evidence_id,
                "intake_hash": self.intake_hash,
                "source_hash": self.source_hash,
                "provenance_chain": sorted(self.provenance_chain),
                "evidence_type": self.evidence_type,
                "status": self.status,
            },
            sort_keys=True,
        ).encode("utf-8")
        return sha256(canonical).hexdigest()


def build_provenance_chain(intake_hash: str, source_hash: str) -> List[str]:
    """Build a deterministic provenance chain from intake and source hashes."""
    if not intake_hash or not source_hash:
        return []
    step1 = sha256(intake_hash.encode("utf-8")).hexdigest()
    step2 = sha256((step1 + source_hash).encode("utf-8")).hexdigest()
    return [intake_hash, step1, step2]


def build_evidence_packet(
    evidence_id: str,
    intake_hash: str,
    source_hash: str,
    evidence_type: str,
    authority: Authority,
    provenance_chain: List[str] | None = None,
) -> SourceEvidencePacket:
    """Build a SourceEvidencePacket. Missing provenance => fail closed."""
    if not authority.is_locked():
        raise ValueError("authority must be locked")

    # Missing provenance => fail closed
    if not intake_hash or not source_hash:
        chain: List[str] = []
        status = "not_computable"
    else:
        chain = provenance_chain if provenance_chain is not None else build_provenance_chain(intake_hash, source_hash)
        status = "valid" if chain else "not_computable"

    return SourceEvidencePacket(
        evidence_id=evidence_id,
        intake_hash=intake_hash,
        source_hash=source_hash,
        provenance_chain=chain,
        evidence_type=evidence_type,
        authority=authority,
        status=status,
    )
