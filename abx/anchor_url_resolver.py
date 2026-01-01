from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _utc_stamp() -> str:
    return _utc_now().strftime("%Y%m%dT%H%M%SZ")


def _read_json(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _write_json(path: str, obj: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def _read_jsonl(path: str) -> List[Dict[str, Any]]:
    if not path or not os.path.exists(path):
        return []
    out: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                if isinstance(d, dict):
                    out.append(d)
            except Exception:
                continue
    return out


def _extract_url_from_anchor(a: Dict[str, Any]) -> str:
    for k in ("url", "canonical_url", "final_url", "source_url", "link"):
        v = a.get(k)
        if isinstance(v, str) and v.strip().startswith("http"):
            return v.strip()
    art = a.get("artifacts") if isinstance(a.get("artifacts"), dict) else {}
    for k in ("url", "canonical_url", "final_url", "source_url", "link"):
        v = art.get(k)
        if isinstance(v, str) and v.strip().startswith("http"):
            return v.strip()
    return ""


def main() -> int:
    ap = argparse.ArgumentParser(
        description="WO-100: resolve anchor_id->url and decorate acquisition batches"
    )
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--in", dest="in_path", required=True, help="acq_batch_*.json")
    ap.add_argument("--anchor-ledger", default="out/ledger/anchor_ledger.jsonl")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    batch = _read_json(args.in_path)
    tasks = batch.get("tasks") if isinstance(batch.get("tasks"), list) else []

    anchors = _read_jsonl(args.anchor_ledger)
    amap: Dict[str, str] = {}
    for a in anchors:
        if not isinstance(a, dict):
            continue
        aid = str(a.get("anchor_id") or "")
        if not aid:
            continue
        url = _extract_url_from_anchor(a)
        if url:
            amap[aid] = url

    changed = 0
    out_tasks = []
    for t in tasks:
        if not isinstance(t, dict):
            continue
        art = t.get("artifacts") if isinstance(t.get("artifacts"), dict) else {}
        aid = str(art.get("anchor_id") or "")
        if aid and (
            not isinstance(art.get("url"), str)
            or not str(art.get("url")).startswith("http")
        ):
            url = amap.get(aid, "")
            if url:
                art = dict(art)
                art["url"] = url
                t = dict(t)
                t["artifacts"] = art
                changed += 1
        out_tasks.append(t)

    out_batch = dict(batch)
    out_batch["tasks"] = out_tasks
    out_batch["notes"] = (
        str(out_batch.get("notes") or "")
        + f" | WO-100 anchor_url_resolver changed={changed}"
    )

    stamp = _utc_stamp()
    out_path = args.out or os.path.join(
        "out/batches", f"acq_batch_resolved_{stamp}.json"
    )
    _write_json(out_path, out_batch)
    print(f"[ANCHOR_URL] wrote: {out_path} changed={changed} tasks={len(out_tasks)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
