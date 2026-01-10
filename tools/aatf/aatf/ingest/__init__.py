from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from ..provenance import sha256_hex
from ..storage import append_ledger, store_blob, upsert_queue_item
from ..queue.states import QueueState
from .canonicalize import canonicalize
from .chunking import chunk_text
from .loaders import load_text_for_kind


def ingest_file(path: str, tags: List[str], kind: str = "auto") -> Dict[str, str | List[str]]:
    source_path = Path(path)
    if not source_path.exists():
        return {"status": "error", "error": "missing_file", "path": path}
    try:
        raw_text, content_type = load_text_for_kind(source_path, kind=kind)
    except RuntimeError as exc:
        return {"status": "error", "error": "unsupported_format", "detail": str(exc)}

    canonical = canonicalize(raw_text, source_path, content_type)
    source_hash = sha256_hex(canonical.text)
    chunks = chunk_text(canonical.text)
    content_payload = {
        "canonical_text": canonical.text,
        "chunks": [chunk.__dict__ for chunk in chunks],
    }
    metadata = {
        "source_hash": source_hash,
        "content_type": content_type,
        "source_path": str(source_path),
        "tags": sorted(tags),
        "canonical_meta": canonical.meta,
    }
    content_id = store_blob(content_payload, metadata)
    item_id = sha256_hex(f"{source_hash}:{source_path.resolve()}")

    queue_item = {
        "item_id": item_id,
        "source_hash": source_hash,
        "source_path": str(source_path),
        "content_type": content_type,
        "state": QueueState.READY.value,
        "tags": sorted(tags),
        "content_id": content_id,
    }
    upsert_queue_item(queue_item)
    append_ledger("INGESTED", {"item_id": item_id, "content_id": content_id})
    append_ledger("QUEUED", {"item_id": item_id, "state": QueueState.READY.value})

    return {
        "status": "ok",
        "item_id": item_id,
        "source_hash": source_hash,
        "chunk_ids": [chunk.chunk_id for chunk in chunks],
    }
