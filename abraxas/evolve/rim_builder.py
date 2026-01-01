from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _read_jsonl(path: Optional[str], max_lines: int = 5000) -> List[Dict[str, Any]]:
    if not path or not os.path.exists(path):
        return []
    out: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= max_lines:
                break
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if isinstance(obj, dict):
                out.append(obj)
    return out


def _write_json(path: str, obj: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)


def build_rim_from_osh_ledger(
    *,
    run_id: str,
    out_root: str,
    osh_ledger_path: Optional[str],
    max_items: int = 200,
    ts: Optional[str] = None,
) -> Tuple[str, Dict[str, Any]]:
    """
    v0.1: Build replay manifest from OSH fetch artifacts ledger.
    Includes only status=ok rows with artifact.body_sha256.
    """
    ts = ts or _utc_now_iso()
    rows = _read_jsonl(osh_ledger_path)

    items: List[Dict[str, Any]] = []
    for row in rows:
        if row.get("status") != "ok":
            continue
        artifact = row.get("artifact") or {}
        if not isinstance(artifact, dict):
            continue
        sha = artifact.get("body_sha256")
        url = artifact.get("url")
        artifact_id = artifact.get("artifact_id")
        fetched_ts = artifact.get("fetched_ts") or row.get("ts")
        if not sha or not (url or artifact_id):
            continue
        ref = str(artifact_id or url)
        item_id = _sha(f"{run_id}:{ref}:{sha}")[:16]
        items.append(
            {
                "item_id": item_id,
                "kind": "fetch_artifact",
                "ref": ref,
                "sha256": str(sha),
                "ts": str(fetched_ts) if fetched_ts else None,
                "meta": {
                    "url": url,
                    "content_type": artifact.get("content_type"),
                    "status_code": artifact.get("status_code"),
                },
            }
        )

    seen = set()
    uniq: List[Dict[str, Any]] = []
    for item in sorted(
        items,
        key=lambda x: (x.get("ref", ""), x.get("sha256", ""), x.get("item_id", "")),
    ):
        key = (item.get("ref"), item.get("sha256"))
        if key in seen:
            continue
        seen.add(key)
        uniq.append(item)
        if len(uniq) >= max_items:
            break

    manifest = {
        "version": "rim.v0.1",
        "run_id": run_id,
        "ts": ts,
        "selection_policy": {
            "max_items": max_items,
            "source": "osh_ledger_ok_only",
        },
        "items": uniq,
        "totals": {"items": len(uniq)},
        "provenance": {
            "builder": "rim_builder.v0.1",
            "inputs": {"osh_ledger": osh_ledger_path},
        },
    }

    out_dir = os.path.join(out_root, run_id)
    out_path = os.path.join(out_dir, "manifest.json")
    _write_json(out_path, manifest)
    return out_path, {"items": len(uniq)}
