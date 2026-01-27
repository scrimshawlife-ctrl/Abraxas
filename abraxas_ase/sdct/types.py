from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from ..provenance import sha256_hex, stable_json_dumps


@dataclass(frozen=True)
class DomainDescriptor:
    domain_id: str
    domain_name: str
    domain_version: str
    motif_kind: str
    alphabet: str
    constraints: List[str]
    params_schema_id: str


@dataclass(frozen=True)
class Motif:
    domain_id: str
    motif_id: str
    motif_text: str
    motif_len: int
    motif_complexity: float
    lane_hint: str


@dataclass(frozen=True)
class EvidenceRow:
    domain_id: str
    motif_id: str
    item_id: str
    source: str
    event_key: str
    mentions: int
    signals: Dict[str, float] = field(default_factory=dict)
    tags: Dict[str, Any] = field(default_factory=dict)
    provenance: Dict[str, Any] = field(default_factory=dict)


def motif_id_from_text(domain_id: str, motif_kind: str, motif_text: str) -> str:
    return f"{domain_id}:{motif_kind}:{motif_text}"


def stable_json(obj: Any) -> str:
    return stable_json_dumps(obj)


def stable_hash(obj: Any) -> str:
    return sha256_hex(stable_json_dumps(obj).encode("utf-8"))
