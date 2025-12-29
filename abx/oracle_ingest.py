from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _sha256(s: str) -> str:
    return hashlib.sha256((s or "").encode("utf-8")).hexdigest()


def _append_jsonl(path: str, obj: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def ingest_text(
    *,
    ledger: str,
    run_id: str,
    oracle_id: str,
    text: str,
    ts_iso: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    ts = ts_iso or _utc_now_iso()
    oid = oracle_id or _sha256(f"{ts}:{text}")[:16]
    obj = {
        "kind": "oracle_run",
        "ts": ts,
        "run_id": run_id,
        "oracle_id": oid,
        "text": text,
        "text_sha256": _sha256(text),
        "meta": meta or {},
    }
    _append_jsonl(ledger, obj)
    return obj


def _read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def main() -> int:
    ap = argparse.ArgumentParser(description="Ingest oracle runs into oracle ledger")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--ledger", default="out/ledger/oracle_runs.jsonl")
    ap.add_argument("--text", default="", help="Raw oracle text")
    ap.add_argument("--file", default="", help="Path to file containing oracle text")
    ap.add_argument(
        "--dir", default="", help="Directory to ingest *.txt/*.md/*.json (best-effort)"
    )
    ap.add_argument("--oracle-id", default="")
    ap.add_argument("--ts", default="")
    args = ap.parse_args()

    if args.text:
        obj = ingest_text(
            ledger=args.ledger,
            run_id=args.run_id,
            oracle_id=args.oracle_id,
            text=args.text,
            ts_iso=args.ts or None,
        )
        print(f"[ORACLE_INGEST] appended oracle_id={obj['oracle_id']}")
        return 0

    if args.file:
        txt = _read_file(args.file)
        obj = ingest_text(
            ledger=args.ledger,
            run_id=args.run_id,
            oracle_id=args.oracle_id,
            text=txt,
            ts_iso=args.ts or None,
            meta={"source_file": args.file},
        )
        print(f"[ORACLE_INGEST] appended oracle_id={obj['oracle_id']} file={args.file}")
        return 0

    if args.dir:
        n = 0
        for root, _, files in os.walk(args.dir):
            for fn in files:
                if not any(fn.lower().endswith(x) for x in [".txt", ".md", ".json"]):
                    continue
                path = os.path.join(root, fn)
                try:
                    txt = _read_file(path)
                    meta = {"source_file": path}
                    ingest_text(
                        ledger=args.ledger,
                        run_id=args.run_id,
                        oracle_id="",
                        text=txt,
                        ts_iso=None,
                        meta=meta,
                    )
                    n += 1
                except Exception:
                    continue
        print(f"[ORACLE_INGEST] ingested {n} files from dir={args.dir}")
        return 0

    raise SystemExit("Provide --text or --file or --dir")


if __name__ == "__main__":
    raise SystemExit(main())
