from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from .config import ensure_paths, resolve_paths
from .provenance import make_event, sha256_hex, stable_dumps

QUEUE_STATE_FILE = "queue_state.json"
LEDGER_FILE = "ledger.jsonl"


def store_blob(content: Dict[str, Any], metadata: Dict[str, Any]) -> str:
    paths = resolve_paths()
    ensure_paths(paths)
    payload = stable_dumps(content)
    content_hash = sha256_hex(payload)
    blob_path = paths.local_store / f"{content_hash}.json"
    meta_path = paths.local_store / f"{content_hash}.meta.json"
    if not blob_path.exists():
        blob_path.write_text(payload, encoding="utf-8")
    meta_path.write_text(stable_dumps(metadata), encoding="utf-8")
    return content_hash


def load_blob(content_hash: str) -> Dict[str, Any]:
    paths = resolve_paths()
    blob_path = paths.local_store / f"{content_hash}.json"
    return json.loads(blob_path.read_text(encoding="utf-8"))


def append_ledger(event_type: str, payload: Dict[str, Any]) -> None:
    paths = resolve_paths()
    ensure_paths(paths)
    event = make_event(event_type, payload)
    ledger_path = paths.ledger / LEDGER_FILE
    with ledger_path.open("a", encoding="utf-8") as handle:
        handle.write(stable_dumps(event) + "\n")


def load_queue_state() -> Dict[str, Any]:
    paths = resolve_paths()
    ensure_paths(paths)
    state_path = paths.local_store / QUEUE_STATE_FILE
    if not state_path.exists():
        return {"items": []}
    return json.loads(state_path.read_text(encoding="utf-8"))


def save_queue_state(state: Dict[str, Any]) -> None:
    paths = resolve_paths()
    ensure_paths(paths)
    state_path = paths.local_store / QUEUE_STATE_FILE
    state["items"] = sorted(state.get("items", []), key=lambda item: item["item_id"])
    state_path.write_text(stable_dumps(state), encoding="utf-8")


def upsert_queue_item(item: Dict[str, Any]) -> None:
    state = load_queue_state()
    items: List[Dict[str, Any]] = state.get("items", [])
    existing = next((i for i in items if i["item_id"] == item["item_id"]), None)
    if existing:
        existing.update(item)
    else:
        items.append(item)
    state["items"] = items
    save_queue_state(state)


def list_queue_items(state: str | None = None) -> List[Dict[str, Any]]:
    items = load_queue_state().get("items", [])
    if state:
        items = [item for item in items if item.get("state") == state]
    return sorted(items, key=lambda item: item["item_id"])


def update_queue_state(item_id: str, updates: Dict[str, Any]) -> Dict[str, Any] | None:
    state = load_queue_state()
    items = state.get("items", [])
    for item in items:
        if item.get("item_id") == item_id:
            item.update(updates)
            save_queue_state(state)
            return item
    return None
