from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Protocol


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
class NormalizedEvidence:
    domain_id: str
    motif_id: str
    item_id: str
    source: str
    event_key: str
    mentions: int
    signals: Dict[str, float] = field(default_factory=dict)
    tags: Dict[str, Any] = field(default_factory=dict)
    provenance: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AggregatedMotifStats:
    domain_id: str
    motif_id: str
    lane: str
    mentions_total: int
    sources_count: int
    events_count: int
    sas: float
    tap_max: float
    pfdi_max: float


class SymbolicDomainCartridge(Protocol):
    def descriptor(self) -> DomainDescriptor: ...

    def encode(self, item: Dict[str, Any]) -> Any: ...

    def extract_motifs(self, sym: Any) -> List[Motif]: ...

    def emit_evidence(
        self,
        item: Dict[str, Any],
        motifs: List[Motif],
        event_key: str,
    ) -> List[NormalizedEvidence]: ...
