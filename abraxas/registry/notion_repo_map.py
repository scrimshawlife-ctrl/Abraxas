from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import hashlib
import json

import yaml


@dataclass(frozen=True)
class NotionRepoMapResult:
    map_id: str
    bindings: list[dict[str, Any]]
    canonical_hash: str


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def load_notion_repo_map(path: str | Path = ".aal/notion_repo_map.v1.yaml") -> NotionRepoMapResult:
    map_path = Path(path)
    if not map_path.exists():
        raise FileNotFoundError(f"Notion repo map not found: {map_path}")

    with map_path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)

    if not isinstance(raw, dict):
        raise ValueError("Notion repo map must decode to an object")
    if raw.get("schema_version") != "NotionRepoMap.v1":
        raise ValueError("Invalid schema")

    map_id = raw.get("map_id")
    bindings = raw.get("bindings")
    if not isinstance(map_id, str) or not map_id:
        raise ValueError("map_id must be a non-empty string")
    if not isinstance(bindings, list):
        raise ValueError("bindings must be a list")

    canonical = json.dumps(raw, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return NotionRepoMapResult(
        map_id=map_id,
        bindings=bindings,
        canonical_hash=_sha256_text(canonical),
    )
