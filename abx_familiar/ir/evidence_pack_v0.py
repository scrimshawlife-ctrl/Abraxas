"""
EvidencePack.v0

Deterministic, hashable container for evidence references gathered by FAMILIAR.

This IR contains NO inference logic and NO summarization requirements.
It stores provenance + minimal descriptors + explicit missing-input flags.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import hashlib
import json


# -------------------------
# Canonical Enums (v0)
# -------------------------

SOURCE_TYPES = {"web", "file", "sensor", "none"}
CONFIDENCE_CLASSES = {"low", "medium", "high", "unknown"}


# -------------------------
# Helpers
# -------------------------

def _stable_json(data: Dict[str, Any]) -> str:
    """
    Produce a stable JSON string for hashing.
    Sorting and separators are fixed to guarantee determinism.
    """
    return json.dumps(
        data,
        sort_keys=True,
        ensure_ascii=True,
        separators=(",", ":"),
    )


def _hash_payload(payload: Dict[str, Any]) -> str:
    """
    Canonical hash function for EvidencePack.
    """
    stable = _stable_json(payload)
    return hashlib.sha256(stable.encode("utf-8")).hexdigest()


# -------------------------
# IR Definitions
# -------------------------

@dataclass(frozen=True)
class EvidenceItem:
    """
    EvidenceItem.v0

    A single evidence reference. Contents are optional and may be omitted
    to avoid copying large text; provenance must still be present.

    Rules:
    - If source_type is "none", url/path/source_id should be None.
    - provenance_hash should be a deterministic hash of the raw retrieved
      artifact when available; otherwise None + explicit missing_fields.
    """

    evidence_id: str
    source_type: str  # web | file | sensor | none

    # Locator fields (exactly one may be used depending on source_type)
    url: Optional[str] = None
    path: Optional[str] = None
    source_id: Optional[str] = None  # e.g., sensor id, connector id, etc.

    # Temporal metadata (ISO-8601 string recommended; caller responsibility)
    timestamp: Optional[str] = None

    # Provenance and confidence
    provenance_hash: Optional[str] = None
    confidence_class: str = "unknown"

    # Optional lightweight metadata (never required)
    meta: Dict[str, Any] = field(default_factory=dict)

    # Explicit flags
    not_computable: bool = False
    missing_fields: List[str] = field(default_factory=list)

    def validate(self) -> None:
        if self.source_type not in SOURCE_TYPES:
            raise ValueError(f"Invalid source_type: {self.source_type}")

        if self.confidence_class not in CONFIDENCE_CLASSES:
            raise ValueError(f"Invalid confidence_class: {self.confidence_class}")

        if self.source_type == "none":
            if self.url is not None or self.path is not None or self.source_id is not None:
                raise ValueError('source_type="none" requires url/path/source_id to be None')

        # Locator sanity: do not enforce exactly-one (some sources may have both),
        # but require at least one locator when source_type != "none".
        if self.source_type != "none":
            if self.url is None and self.path is None and self.source_id is None:
                raise ValueError("Non-'none' source_type requires at least one locator (url/path/source_id)")

        if self.not_computable and not self.missing_fields:
            raise ValueError("not_computable=True requires missing_fields to be non-empty")

    def to_payload(self) -> Dict[str, Any]:
        # Ensure deterministic ordering by explicit key listing
        return {
            "evidence_id": self.evidence_id,
            "source_type": self.source_type,
            "url": self.url,
            "path": self.path,
            "source_id": self.source_id,
            "timestamp": self.timestamp,
            "provenance_hash": self.provenance_hash,
            "confidence_class": self.confidence_class,
            "meta": self.meta,
            "not_computable": self.not_computable,
            "missing_fields": list(self.missing_fields),
        }

    def hash(self) -> str:
        self.validate()
        return _hash_payload(self.to_payload())


@dataclass(frozen=True)
class EvidencePack:
    """
    EvidencePack.v0

    Rules:
    - Pure container: holds evidence references only.
    - No derived fields; no synthesis; no scoring beyond confidence_class tags.
    """

    pack_id: str
    items: List[EvidenceItem] = field(default_factory=list)

    # Optional note about collection context (never required)
    collection_context: Dict[str, Any] = field(default_factory=dict)

    # Explicit flags
    not_computable: bool = False
    missing_fields: List[str] = field(default_factory=list)

    def validate(self) -> None:
        if not isinstance(self.items, list):
            raise ValueError("items must be a list")

        for it in self.items:
            if not isinstance(it, EvidenceItem):
                raise ValueError("items must contain EvidenceItem objects")
            it.validate()

        if self.not_computable and not self.missing_fields:
            raise ValueError("not_computable=True requires missing_fields to be non-empty")

    def to_payload(self) -> Dict[str, Any]:
        return {
            "pack_id": self.pack_id,
            "items": [it.to_payload() for it in self.items],
            "collection_context": self.collection_context,
            "not_computable": self.not_computable,
            "missing_fields": list(self.missing_fields),
        }

    def hash(self) -> str:
        self.validate()
        return _hash_payload(self.to_payload())

    def semantically_equal(self, other: "EvidencePack") -> bool:
        if not isinstance(other, EvidencePack):
            return False
        return self.hash() == other.hash()
