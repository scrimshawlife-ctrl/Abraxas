from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _norm_url(url: str) -> str:
    u = (url or "").strip()
    # minimal normalization (no network calls):
    u = u.replace("http://", "https://")
    # remove trailing slash noise
    if u.endswith("/"):
        u = u[:-1]
    return u


def url_hash(url: str) -> str:
    u = _norm_url(url)
    return hashlib.sha256(u.encode("utf-8")).hexdigest()


def anchor_id(run_id: str, term: str, url_or_note_hash: str) -> str:
    base = f"{run_id}|{(term or '').strip().lower()}|{url_or_note_hash}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:20]


def domain_from_url(url: str) -> str:
    u = _norm_url(url)
    # cheap parse; avoid urllib edge complexity
    try:
        # https://domain/path
        rest = u.split("://", 1)[1]
        dom = rest.split("/", 1)[0]
        return dom.lower()
    except Exception:
        return ""


def append_anchor(
    *,
    ledger_path: str,
    run_id: str,
    term: str,
    url: str = "",
    offline_note: str = "",
    source_mode: str = "manual",
    evidence_type: str = "article",
    primary: bool = False,
    tags: Optional[List[str]] = None,
    claims: Optional[List[str]] = None,
) -> Dict[str, Any]:
    os.makedirs(os.path.dirname(ledger_path), exist_ok=True)

    tags = tags or []
    claims = claims or []

    u = _norm_url(url) if url else ""
    uh = url_hash(u) if u else ""

    note_hash = hashlib.sha256((offline_note or "").encode("utf-8")).hexdigest() if offline_note else ""
    key_hash = uh if uh else note_hash
    aid = anchor_id(run_id, term, key_hash)

    entry = {
        "kind": "anchor_added",
        "ts": _utc_now_iso(),
        "anchor_id": aid,
        "run_id": run_id,
        "term": term,
        "source_mode": source_mode,
        "evidence_type": evidence_type,
        "primary": bool(primary),
        "url": u or None,
        "url_hash": uh or None,
        "domain": domain_from_url(u) if u else None,
        "offline_note_hash": note_hash or None,
        "tags": [str(x) for x in tags],
        "claims": [str(x) for x in claims],
        "notes": "Append-only evidence atom. Used for Proof Integrity Score and anti-Goodhart defenses.",
    }

    with open(ledger_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def main() -> int:
    ap = argparse.ArgumentParser(description="Append anchor evidence to anchor ledger (append-only)")
    ap.add_argument("--ledger", default="out/ledger/anchor_ledger.jsonl")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--term", required=True)
    ap.add_argument("--url", default="")
    ap.add_argument("--offline-note", default="")
    ap.add_argument("--source-mode", default="manual", choices=["manual", "offline", "online", "decodo", "api"])
    ap.add_argument("--evidence-type", default="article")
    ap.add_argument("--primary", action="store_true")
    ap.add_argument("--tag", action="append", default=[])
    ap.add_argument("--claim", action="append", default=[])
    args = ap.parse_args()

    if not args.url and not args.offline_note:
        raise SystemExit("Provide --url or --offline-note")

    entry = append_anchor(
        ledger_path=args.ledger,
        run_id=str(args.run_id),
        term=str(args.term),
        url=str(args.url),
        offline_note=str(args.offline_note),
        source_mode=str(args.source_mode),
        evidence_type=str(args.evidence_type),
        primary=bool(args.primary),
        tags=list(args.tag or []),
        claims=list(args.claim or []),
    )
    print(f"[ANCHOR_LEDGER] appended anchor_id={entry['anchor_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
