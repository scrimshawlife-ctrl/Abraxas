"""Storage index for deterministic lifecycle decisions."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from abraxas.core.canonical import canonical_json


@dataclass(frozen=True)
class StorageIndexEntry:
    artifact_type: str
    source_id: str
    created_at_utc: str
    size_bytes: int
    codec: str
    tier: str
    path: str
    content_hash: str
    last_accessed_at_utc: Optional[str] = None
    superseded_by: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_type": self.artifact_type,
            "source_id": self.source_id,
            "created_at_utc": self.created_at_utc,
            "size_bytes": self.size_bytes,
            "codec": self.codec,
            "tier": self.tier,
            "path": self.path,
            "content_hash": self.content_hash,
            "last_accessed_at_utc": self.last_accessed_at_utc,
            "superseded_by": self.superseded_by,
        }


class StorageIndex:
    def __init__(self, entries: Optional[List[StorageIndexEntry]] = None) -> None:
        self.entries = entries or []

    def add(self, entry: StorageIndexEntry) -> None:
        self.entries.append(entry)

    def sorted_entries(self) -> List[StorageIndexEntry]:
        return sorted(self.entries, key=_entry_sort_key)

    def to_jsonl(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            for entry in self.sorted_entries():
                f.write(canonical_json(entry.to_dict()) + "\n")

    @classmethod
    def from_jsonl(cls, path: Path) -> "StorageIndex":
        if not path.exists():
            return cls([])
        entries: List[StorageIndexEntry] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            entries.append(StorageIndexEntry(**payload))
        return cls(entries)


def _entry_sort_key(entry: StorageIndexEntry) -> tuple:
    return (
        entry.artifact_type,
        entry.created_at_utc,
        entry.path,
        entry.content_hash,
    )
