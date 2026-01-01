from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Tuple

try:
    import yaml  # type: ignore
except Exception:
    yaml = None  # optional

from .schemas import CanonEntry, Provenance, Rune


def _sha256_bytes(b: bytes) -> str:
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()


def _read_text_bytes(path: Path) -> bytes:
    data = path.read_bytes()
    # Deterministic: do not normalize line endings; hash raw bytes
    return data


def _load_yaml_or_json(path: Path) -> Tuple[Dict[str, Any], bytes]:
    raw = _read_text_bytes(path)
    suffix = path.suffix.lower()
    if suffix in (".json", ".rune.json"):
        return json.loads(raw.decode("utf-8")), raw
    if suffix in (".yaml", ".yml"):
        if yaml is None:
            return json.loads(raw.decode("utf-8")), raw
        return yaml.safe_load(raw.decode("utf-8")), raw
    raise RuntimeError(f"Unsupported codex artifact type: {path.suffix} ({path})")


def _require(obj: Dict[str, Any], k: str) -> Any:
    if k not in obj:
        raise KeyError(f"Missing required field: {k}")
    return obj[k]


def load_canon_entry(path: Path) -> CanonEntry:
    obj, raw = _load_yaml_or_json(path)
    prov = _require(obj, "provenance")
    p = Provenance(
        spec=str(_require(prov, "spec")),
        created_utc=str(_require(prov, "created_utc")),
        author=str(_require(prov, "author")),
        hash_alg="sha256",
        content_sha256=_sha256_bytes(raw),
    )
    body = _require(obj, "body")
    if not isinstance(body, dict):
        raise TypeError("canon.body must be a mapping of MODE -> text")
    return CanonEntry(
        entry_id=str(_require(obj, "entry_id")),
        title=str(_require(obj, "title")),
        status=str(_require(obj, "status")),
        scope=list(_require(obj, "scope")),
        modes=list(_require(obj, "modes")),
        body={str(k): str(v) for k, v in sorted(body.items(), key=lambda kv: str(kv[0]))},
        tags=sorted([str(t) for t in list(_require(obj, "tags"))]),
        provenance=p,
    )


def load_rune(path: Path) -> Rune:
    obj, raw = _load_yaml_or_json(path)
    prov = _require(obj, "provenance")
    p = Provenance(
        spec=str(_require(prov, "spec")),
        created_utc=str(_require(prov, "created_utc")),
        author=str(_require(prov, "author")),
        hash_alg="sha256",
        content_sha256=_sha256_bytes(raw),
    )
    return Rune(
        rune_id=str(_require(obj, "rune_id")),
        name=str(_require(obj, "name")),
        family=str(_require(obj, "family")),
        version=str(_require(obj, "version")),
        bindings=dict(_require(obj, "bindings")),
        glyph_hint=dict(_require(obj, "glyph_hint")),
        canon_refs=sorted([str(x) for x in list(_require(obj, "canon_refs"))]),
        provenance=p,
    )
