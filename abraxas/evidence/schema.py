from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Literal


SourceType = Literal["url", "pdf", "screenshot", "manual_note", "dataset"]


@dataclass(frozen=True)
class EvidenceClaim:
    text: str
    quote: str = ""
    entities: List[str] | None = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if d["entities"] is None:
            d["entities"] = []
        return d


@dataclass(frozen=True)
class EvidenceBundle:
    bundle_id: str
    terms: List[str]
    source_type: SourceType
    source_ref: str
    captured_ts: str
    claims: List[Dict[str, Any]]
    credence: float
    provenance: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
