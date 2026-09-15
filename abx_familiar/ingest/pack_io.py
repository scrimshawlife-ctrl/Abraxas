"""Load local EvidencePack.v0 JSON (items[] IR)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from abx_familiar.ir.evidence_pack_v0 import EvidenceItem, EvidencePack


def item_from_dict(raw: dict[str, Any]) -> EvidenceItem:
    return EvidenceItem(
        evidence_id=str(raw.get("evidence_id") or ""),
        source_type=str(raw.get("source_type") or "none"),
        url=raw.get("url"),
        path=raw.get("path"),
        source_id=raw.get("source_id"),
        timestamp=raw.get("timestamp"),
        provenance_hash=raw.get("provenance_hash"),
        confidence_class=str(raw.get("confidence_class") or "unknown"),
        meta=raw.get("meta") if isinstance(raw.get("meta"), dict) else {},
        not_computable=bool(raw.get("not_computable", False)),
        missing_fields=list(raw.get("missing_fields") or []),
    )


def load_evidence_pack(path: str | Path) -> EvidencePack:
    raw = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("pack root is not an object")
    items_raw = raw.get("items") if isinstance(raw.get("items"), list) else []
    items = [item_from_dict(row) for row in items_raw if isinstance(row, dict)]
    pack = EvidencePack(
        pack_id=str(raw.get("pack_id") or ""),
        items=items,
        collection_context=raw.get("collection_context")
        if isinstance(raw.get("collection_context"), dict)
        else {},
        not_computable=bool(raw.get("not_computable", False)),
        missing_fields=list(raw.get("missing_fields") or []),
    )
    pack.validate()
    return pack
