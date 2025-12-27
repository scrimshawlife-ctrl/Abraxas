from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_jsonl(path: str) -> List[Dict[str, Any]]:
    if not path or not os.path.exists(path):
        return []
    out = []
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


def _append_jsonl(path: str, obj: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _domain_group(domain: str) -> str:
    d = (domain or "").lower()
    if any(
        x in d
        for x in [
            "tiktok.com",
            "instagram.com",
            "youtube.com",
            "reddit.com",
            "twitter.com",
            "x.com",
        ]
    ):
        return "social"
    if any(
        x in d
        for x in [
            "wikipedia.org",
            "nih.gov",
            "nature.com",
            "science.org",
            "arxiv.org",
        ]
    ):
        return "reference"
    if any(
        x in d
        for x in [
            "nytimes.com",
            "bbc.co.uk",
            "reuters.com",
            "apnews.com",
            "theguardian.com",
        ]
    ):
        return "mainstream"
    if not d:
        return "none"
    return "other"


TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9_\-']{1,}")


def _tokenize(text: str) -> List[str]:
    return [m.group(0).lower() for m in TOKEN.finditer(text or "")]


def _find_concordance(
    term: str, text: str, window: int = 64, max_snips: int = 6
) -> List[str]:
    t = (term or "").strip()
    if not t or not text:
        return []
    out = []
    low = text.lower()
    needle = t.lower()
    start = 0
    while len(out) < max_snips:
        idx = low.find(needle, start)
        if idx < 0:
            break
        a = max(0, idx - window)
        b = min(len(text), idx + len(t) + window)
        snip = text[a:b].replace("\n", " ").strip()
        out.append(snip)
        start = idx + len(t)
    return out


def _co_terms(term: str, tokens: List[str], span: int = 6) -> Counter:
    t = (term or "").lower().strip()
    if not t or not tokens:
        return Counter()
    out = Counter()
    if " " in t:
        return out
    for i, tok in enumerate(tokens):
        if tok != t:
            continue
        lo = max(0, i - span)
        hi = min(len(tokens), i + span + 1)
        for j in range(lo, hi):
            if j == i:
                continue
            ct = tokens[j]
            if len(ct) < 3 or ct == t:
                continue
            out[ct] += 1
    return out


def _compress_definition(term: str, co: Counter, groups: Counter) -> str:
    top_co = [w for (w, _) in co.most_common(8)]
    top_g = [g for (g, _) in groups.most_common(3) if g and g != "none"]
    bits = []
    if top_co:
        bits.append("contexts: " + ", ".join(top_co))
    if top_g:
        bits.append("domains: " + ", ".join(top_g))
    if not bits:
        return f"{term}: insufficient context yet (await more anchors/runs)."
    return f"{term}: " + " | ".join(bits)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="WO-91: enrich AAlmanac canon entries deterministically from concordance + co-terms"
    )
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--aalmanac", default="out/ledger/aalmanac.jsonl")
    ap.add_argument("--oracle-ledger", default="out/ledger/oracle_runs.jsonl")
    ap.add_argument("--anchor-ledger", default="out/ledger/anchor_ledger.jsonl")
    ap.add_argument("--events-ledger", default="out/ledger/aalmanac_events.jsonl")
    ap.add_argument("--out", default="")
    ap.add_argument("--max-terms", type=int, default=40)
    ap.add_argument("--max-snips", type=int, default=6)
    args = ap.parse_args()

    canon = [
        e
        for e in _read_jsonl(args.aalmanac)
        if e.get("kind") == "aalmanac_entry"
        and e.get("tier") == "CANON"
        and e.get("term")
    ]
    canon = canon[-int(args.max_terms) :]
    runs = [r for r in _read_jsonl(args.oracle_ledger) if r.get("kind") == "oracle_run"]
    anchors = _read_jsonl(args.anchor_ledger)

    state_items = []
    for e in canon:
        term = str(e.get("term") or "").strip()
        co = Counter()
        groups = Counter()
        usage = []
        sources = []

        for r in runs[-200:]:
            txt = str(r.get("text") or "")
            if not txt:
                continue
            snips = _find_concordance(
                term,
                txt,
                window=64,
                max_snips=max(1, int(args.max_snips // 2)),
            )
            if snips:
                oid = str(r.get("oracle_id") or "")
                for s in snips:
                    usage.append(
                        {"source_kind": "oracle", "oracle_id": oid, "snippet": s}
                    )
                toks = _tokenize(txt)
                co.update(_co_terms(term, toks, span=6))
                sources.append(("oracle", oid))

        for a in anchors[-500:]:
            title = str(a.get("title") or "")
            hint = str(a.get("content_hint") or "")
            dom = str(a.get("domain") or "")
            blob = (title + "\n" + hint).strip()
            if not blob:
                continue
            snips = _find_concordance(
                term,
                blob,
                window=64,
                max_snips=max(1, int(args.max_snips // 2)),
            )
            if snips:
                aid = str(a.get("anchor_id") or "")
                for s in snips:
                    usage.append(
                        {
                            "source_kind": "anchor",
                            "anchor_id": aid,
                            "domain": dom,
                            "snippet": s,
                        }
                    )
                groups[_domain_group(dom)] += 1
                toks = _tokenize(blob)
                co.update(_co_terms(term, toks, span=6))
                sources.append(("anchor", aid))

        usage = usage[: int(args.max_snips)]
        definition = _compress_definition(term, co, groups)
        motifs = [w for (w, _) in co.most_common(10)]
        dom_tags = [g for (g, _) in groups.most_common(4) if g and g != "none"]

        ev = {
            "kind": "aalmanac_enriched",
            "ts": _utc_now_iso(),
            "run_id": args.run_id,
            "term": term,
            "definition": definition,
            "usage": usage,
            "motifs": motifs,
            "domain_tags": dom_tags,
            "provenance": {
                "sources_sampled": len(sources),
                "oracle_window": 200,
                "anchor_window": 500,
            },
            "notes": "Deterministic enrichment from concordance + co-term counts; not an LLM definition.",
        }
        _append_jsonl(args.events_ledger, ev)
        state_items.append(ev)

    out_obj = {
        "version": "aalmanac_state.v0.1",
        "ts": _utc_now_iso(),
        "run_id": args.run_id,
        "n_terms": len(state_items),
        "items": state_items,
        "notes": "Materialized AAlmanac state derived from canon entries + enrichment events.",
    }

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = args.out or os.path.join(
        "out/reports", f"aalmanac_state_{stamp}.json"
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_obj, f, ensure_ascii=False, indent=2)
    print(f"[AALMANAC_STATE] wrote: {out_path} terms={len(state_items)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
