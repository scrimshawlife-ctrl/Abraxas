from __future__ import annotations

import argparse
import os
from typing import List

from abx.evidence_ledger import (
    EvidenceEvent,
    EvidenceLedger,
    make_note_event,
    make_url_event,
    sha256_file,
)
from abx.media_auth import mav_for_event


def main() -> int:
    p = argparse.ArgumentParser(description="Ingest evidence into append-only ledger")
    p.add_argument("--run-id", required=True)
    p.add_argument("--term", required=True)
    p.add_argument("--ledger", default="out/ledger/evidence_ledger.jsonl")
    p.add_argument("--channel", default="manual_offline")
    p.add_argument("--url", default="")
    p.add_argument("--file", default="")
    p.add_argument("--note", default="")
    p.add_argument("--tags", default="", help="comma-separated tags e.g. primary,gov,transcript")
    p.add_argument("--publisher", default="")
    p.add_argument("--observed-date", default="")
    p.add_argument("--claim", default="")
    p.add_argument("--weight", type=float, default=0.5)
    args = p.parse_args()

    tags: List[str] = []
    if args.tags.strip():
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]

    ledger = EvidenceLedger(args.ledger)

    if args.url.strip():
        base = {
            "kind": "url",
            "source": args.url.strip(),
            "tags": tags,
            "weight": float(args.weight),
        }
        mav = mav_for_event(base)
        ev = make_url_event(
            run_id=args.run_id,
            term=args.term,
            url=args.url.strip(),
            channel=args.channel,
            observed_date=args.observed_date,
            publisher=args.publisher,
            tags=tags,
            weight=float(args.weight),
            claim=args.claim,
            mav=mav,
        )
        ledger.append(ev)
        print("[LEDGER_INGEST] appended url")
        return 0

    if args.file.strip():
        fp = args.file.strip()
        h = sha256_file(fp) or ""
        mav = mav_for_event(
            {"kind": "file", "source": os.path.abspath(fp), "tags": tags, "weight": float(args.weight)}
        )
        ev = EvidenceEvent(
            ts=make_note_event(
                run_id=args.run_id,
                term=args.term,
                note="x",
                channel=args.channel,
            ).ts,
            run_id=args.run_id,
            term=args.term,
            kind="file",
            source=os.path.abspath(fp),
            sha256=h,
            observed_date=args.observed_date,
            publisher=args.publisher,
            channel=args.channel,
            claim=args.claim,
            tags=tags,
            weight=float(args.weight),
            mav=mav,
        )
        ledger.append(ev)
        print("[LEDGER_INGEST] appended file")
        return 0

    if args.note.strip():
        base = {
            "kind": "note",
            "source": args.note.strip(),
            "tags": tags,
            "weight": float(args.weight),
        }
        mav = mav_for_event(base)
        ev = make_note_event(
            run_id=args.run_id,
            term=args.term,
            note=args.note.strip(),
            channel=args.channel,
            tags=tags,
            weight=float(args.weight),
            claim=args.claim,
            mav=mav,
        )
        ledger.append(ev)
        print("[LEDGER_INGEST] appended note")
        return 0

    print("[LEDGER_INGEST] nothing to ingest (provide --url or --file or --note)")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
