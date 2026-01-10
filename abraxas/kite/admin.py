from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from ..io.storage import StoragePaths, read_json, write_json
from .ingest import ensure_candidates
from .models import KiteCandidates


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    out: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(json.loads(line))
    return out


def list_ingests(paths: StoragePaths, day: str) -> List[Dict[str, Any]]:
    return _read_jsonl(paths.kite_ingest_jsonl(day))


def load_candidates(paths: StoragePaths, day: str) -> Dict[str, Any]:
    ensure_candidates(paths, day)
    data = read_json(paths.kite_candidates_path(day))
    if not data:
        return KiteCandidates.empty(day).to_dict()
    return data


def save_candidates(paths: StoragePaths, day: str, payload: Dict[str, Any]) -> None:
    write_json(paths.kite_candidates_path(day), payload)


def add_candidate(paths: StoragePaths, day: str, category: str, item: Dict[str, Any]) -> Dict[str, Any]:
    current = load_candidates(paths, day)
    mapping = {
        "terms": "proposed_terms",
        "metrics": "proposed_metrics",
        "overlays": "proposed_overlays",
    }
    key = mapping.get(category)
    if not key:
        raise ValueError("Invalid candidate category.")
    items = current.get(key, [])
    if not isinstance(items, list):
        items = []
    items.append(item)
    current[key] = items
    save_candidates(paths, day, current)
    return current
