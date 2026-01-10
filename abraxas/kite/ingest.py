from __future__ import annotations

import json
from typing import List, Optional
from pathlib import Path

from ..io.storage import StoragePaths, write_text
from .models import KiteCandidates, KiteIngest


def append_jsonl(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(obj, ensure_ascii=False, sort_keys=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def ingest_note(
    paths: StoragePaths,
    day: str,
    kind: str,
    domain: str,
    tags: List[str],
    text: str,
    source: Optional[str],
) -> None:
    item = KiteIngest.create(kind=kind, domain=domain, tags=tags, text=text, source=source)
    append_jsonl(paths.kite_ingest_jsonl(day), item.to_dict())


def ensure_candidates(paths: StoragePaths, day: str) -> None:
    p = paths.kite_candidates_path(day)
    if p.exists():
        return
    c = KiteCandidates.empty(day)
    write_text(p, json.dumps(c.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n")
