from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .states import QueueState


@dataclass(frozen=True)
class QueueItem:
    item_id: str
    source_hash: str
    source_path: str
    content_type: str
    state: QueueState
    tags: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ReviewDecision:
    item_id: str
    decision: QueueState
    notes: str


@dataclass(frozen=True)
class ExportBundle:
    bundle_id: str
    included_types: List[str]
    file_manifest: List[dict]
    provenance: dict
