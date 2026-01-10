from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class KiteIngest:
    schema: str
    timestamp_utc: str
    kind: str
    domain: str
    tags: List[str]
    text: str
    source: Optional[str] = None

    @staticmethod
    def create(kind: str, domain: str, tags: List[str], text: str, source: Optional[str]) -> "KiteIngest":
        return KiteIngest(
            schema="kite_ingest.v0",
            timestamp_utc=datetime.utcnow().isoformat() + "Z",
            kind=kind,
            domain=domain,
            tags=tags,
            text=text,
            source=source,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": self.schema,
            "timestamp_utc": self.timestamp_utc,
            "kind": self.kind,
            "domain": self.domain,
            "tags": list(self.tags),
            "text": self.text,
            "source": self.source,
        }


@dataclass(frozen=True)
class KiteCandidates:
    schema: str
    day: str
    proposed_terms: List[Dict[str, Any]]
    proposed_metrics: List[Dict[str, Any]]
    proposed_overlays: List[Dict[str, Any]]

    @staticmethod
    def empty(day: str) -> "KiteCandidates":
        return KiteCandidates(
            schema="kite_candidates.v0",
            day=day,
            proposed_terms=[],
            proposed_metrics=[],
            proposed_overlays=[],
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": self.schema,
            "day": self.day,
            "proposed_terms": self.proposed_terms,
            "proposed_metrics": self.proposed_metrics,
            "proposed_overlays": self.proposed_overlays,
        }
