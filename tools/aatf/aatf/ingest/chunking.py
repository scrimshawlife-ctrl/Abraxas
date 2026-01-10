from __future__ import annotations

from typing import Any, Dict, List


def chunk_payload(payload: Dict[str, Any], *, max_items: int = 50) -> List[Dict[str, Any]]:
    items = payload.get("items", [])
    if not isinstance(items, list):
        return [payload]
    chunks = []
    for idx in range(0, len(items), max_items):
        chunk = dict(payload)
        chunk["items"] = items[idx : idx + max_items]
        chunks.append(chunk)
    return chunks
