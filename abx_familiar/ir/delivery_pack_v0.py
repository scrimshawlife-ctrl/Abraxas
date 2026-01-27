"""
DeliveryPack.v0

Deterministic, hashable container for the final output of a FAMILIAR run,
including rendered output and references to supporting artifacts.

Rules:
- Contains no semantic filtering or rewriting.
- Attachments are references (or small structured payloads), not raw corpora.
- Provenance manifest is required (may be minimal in v0.1).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import hashlib
import json


# -------------------------
# Canonical Enums (v0)
# -------------------------

MODES = {"Oracle", "Ritual", "Analyst"}
TIER_SCOPES = {"Psychonaut", "Academic", "Enterprise"}


# -------------------------
# Helpers
# -------------------------

def _stable_json(data: Dict[str, Any]) -> str:
    return json.dumps(
        data,
        sort_keys=True,
        ensure_ascii=True,
        separators=(",", ":"),
    )


def _hash_payload(payload: Dict[str, Any]) -> str:
    stable = _stable_json(payload)
    return hashlib.sha256(stable.encode("utf-8")).hexdigest()


# -------------------------
# IR Definitions
# -------------------------

@dataclass(frozen=True)
class AttachmentRef:
    """
    AttachmentRef.v0

    Reference to a supporting artifact produced during execution.
    """

    kind: str  # e.g., "evidence", "ward_report", "execution_trace", "ledger_entry"
    ref_id: str  # identifier string (hash, filename, db id, etc.)
    meta: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.kind:
            raise ValueError("AttachmentRef.kind must be non-empty")
        if not self.ref_id:
            raise ValueError("AttachmentRef.ref_id must be non-empty")
        if not isinstance(self.meta, dict):
            raise ValueError("AttachmentRef.meta must be a dict")

    def to_payload(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "ref_id": self.ref_id,
            "meta": self.meta,
        }


@dataclass(frozen=True)
class DeliveryPack:
    """
    DeliveryPack.v0
    """

    delivery_id: str

    mode: str
    tier_scope: str

    rendered_output: str  # final text payload for the chosen mode

    attachments: List[AttachmentRef] = field(default_factory=list)

    provenance_manifest: Dict[str, Any] = field(default_factory=dict)

    not_computable: bool = False
    missing_fields: List[str] = field(default_factory=list)

    def validate(self) -> None:
        if self.mode not in MODES:
            raise ValueError(f"Invalid mode: {self.mode}")

        if self.tier_scope not in TIER_SCOPES:
            raise ValueError(f"Invalid tier_scope: {self.tier_scope}")

        if not isinstance(self.rendered_output, str):
            raise ValueError("rendered_output must be a string")

        for a in self.attachments:
            if not isinstance(a, AttachmentRef):
                raise ValueError("attachments must contain AttachmentRef objects")
            a.validate()

        if not isinstance(self.provenance_manifest, dict):
            raise ValueError("provenance_manifest must be a dict")

        if self.not_computable and not self.missing_fields:
            raise ValueError("not_computable=True requires missing_fields to be non-empty")

    def to_payload(self) -> Dict[str, Any]:
        return {
            "delivery_id": self.delivery_id,
            "mode": self.mode,
            "tier_scope": self.tier_scope,
            "rendered_output": self.rendered_output,
            "attachments": [a.to_payload() for a in self.attachments],
            "provenance_manifest": self.provenance_manifest,
            "not_computable": self.not_computable,
            "missing_fields": list(self.missing_fields),
        }

    def hash(self) -> str:
        self.validate()
        return _hash_payload(self.to_payload())

    def semantically_equal(self, other: "DeliveryPack") -> bool:
        if not isinstance(other, DeliveryPack):
            return False
        return self.hash() == other.hash()
