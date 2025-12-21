from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Literal


@dataclass(frozen=True)
class Provenance:
    spec: str
    created_utc: str
    author: str
    hash_alg: Literal["sha256"] = "sha256"
    content_sha256: str = ""  # computed at load time


@dataclass(frozen=True)
class CanonEntry:
    entry_id: str
    title: str
    status: Literal["canon", "draft"]
    scope: List[str]
    modes: List[Literal["OPEN", "ALIGN", "ASCEND", "CLEAR", "SEAL"]]
    body: Dict[str, str]  # mode -> text
    tags: List[str]
    provenance: Provenance


@dataclass(frozen=True)
class Rune:
    rune_id: str
    name: str
    family: Literal["constraint", "operator", "metric", "protocol", "sigil"]
    version: str
    bindings: Dict[str, Any]  # e.g., {"applies_to": [...], "invariants": [...]}
    glyph_hint: Dict[str, Any]  # image generator params / canonical description
    canon_refs: List[str]  # entry_ids
    provenance: Provenance
