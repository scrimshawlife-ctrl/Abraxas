#!/usr/bin/env python3
# abraxas/cli/sco_run.py
# CLI for running SCO/ECO pipeline

from __future__ import annotations
import argparse
import json
import sys

from abraxas.linguistic.transparency import TransparencyLexicon
from abraxas.pipelines.sco_pipeline import SCOPipeline
from abraxas.storage.events import write_events_jsonl

def main() -> int:
    ap = argparse.ArgumentParser(description="Run Abraxas SCO/ECO pipeline on text records.")
    ap.add_argument("--records", required=True, help="JSON file: [{'id':'','text':''}, ...]")
    ap.add_argument("--lexicon", required=True, help="JSON file: [{'canonical':'', 'variants':[...]}]")
    ap.add_argument("--out", required=True, help="Output .jsonl path for events")
    ap.add_argument("--domain", default="general", help="Domain label (music/idiom/brand/slang)")
    ap.add_argument("--sti", default="", help="Optional STI lexicon JSON path (else build from lexicon)")
    args = ap.parse_args()

    with open(args.records, "r", encoding="utf-8") as f:
        records = json.load(f)
    with open(args.lexicon, "r", encoding="utf-8") as f:
        lexicon = json.load(f)

    if args.sti:
        transparency = TransparencyLexicon.load_json(args.sti)
    else:
        # Build STI lexicon from canonical + variants (deterministic bootstrap)
        toks = []
        for e in lexicon:
            toks.append(e["canonical"])
            toks.extend(e.get("variants", []))
        transparency = TransparencyLexicon.build(toks)

    pipe = SCOPipeline(transparency)
    events = pipe.run(records=records, lexicon=lexicon, domain=args.domain)
    write_events_jsonl(args.out, events)

    print(f"[SCO] wrote {len(events)} events to {args.out}")
    print(f"[SCO] transparency_lexicon_provenance={transparency.provenance_sha256}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
