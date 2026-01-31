from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
import json

from aal_core.aalmanac.storage.entries import DEFAULT_AALMANAC_DIR

DEFAULT_INDEX_PATH = DEFAULT_AALMANAC_DIR / "index.json"


def build_index(entries: Iterable[Dict[str, Any]], *, latest_limit: int = 200) -> Dict[str, Any]:
    by_term: Dict[str, List[str]] = {}
    by_domain: Dict[str, List[str]] = {}
    ordered: List[str] = []

    for entry in entries:
        entry_id = str(entry.get("entry_id", ""))
        if not entry_id:
            continue
        term = str(entry.get("term_canonical", ""))
        if term:
            by_term.setdefault(term, []).append(entry_id)
        ctx = entry.get("usage_context", {}) or {}
        domain = str(ctx.get("domain", ""))
        if domain:
            by_domain.setdefault(domain, []).append(entry_id)
        ordered.append(entry_id)

    latest = ordered[-latest_limit:] if latest_limit > 0 else ordered
    return {
        "schema_version": "aal.aalmanac.index.v1",
        "by_term": by_term,
        "by_domain": by_domain,
        "latest": latest,
    }


def write_index(index: Dict[str, Any], *, index_path: Optional[Path] = None) -> None:
    target = index_path or DEFAULT_INDEX_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(index, indent=2, sort_keys=True), encoding="utf-8")
