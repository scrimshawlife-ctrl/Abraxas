from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Set


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


def main() -> int:
    ap = argparse.ArgumentParser(
        description="WO-88: compute slang/motif migration across sources/domains"
    )
    ap.add_argument("--candidates", default="out/ledger/slang_candidates.jsonl")
    ap.add_argument("--out", default="")
    ap.add_argument("--recent-n", type=int, default=1500)
    args = ap.parse_args()

    cands = [
        c for c in _read_jsonl(args.candidates) if c.get("kind") == "slang_candidate"
    ]
    cands = cands[-int(args.recent_n) :]

    by_term = defaultdict(list)
    for c in cands:
        t = str(c.get("term") or "").strip()
        if t:
            by_term[t].append(c)

    items = []
    for term, lst in by_term.items():
        groups: Set[str] = set()
        domains: Set[str] = set()
        sources: Set[str] = set()
        peak = 0.0
        for c in lst:
            sources.add(str(c.get("source_kind") or ""))
            dom = str(c.get("domain") or "")
            if dom:
                domains.add(dom)
                groups.add(_domain_group(dom))
            peak = max(peak, float(c.get("score") or 0.0))
        n_groups = len([g for g in groups if g and g != "none"])
        n_sources = len([s for s in sources if s])

        migration = min(
            1.0, 0.55 * (n_groups / 3.0) + 0.25 * (n_sources / 2.0) + 0.20 * peak
        )
        items.append(
            {
                "term": term,
                "n_mentions": len(lst),
                "domain_groups": sorted(list(groups)),
                "n_domain_groups": n_groups,
                "n_domains": len(domains),
                "source_kinds": sorted(list(sources)),
                "peak_score": float(peak),
                "migration_score": float(migration),
            }
        )

    items.sort(key=lambda x: (-x["migration_score"], -x["n_mentions"], x["term"]))
    obj = {
        "version": "slang_migration.v0.1",
        "ts": _utc_now_iso(),
        "n_terms": len(items),
        "top": items[:200],
        "notes": "Migration indicates cross-domain propagation; not truth or value judgment.",
    }

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = args.out or os.path.join(
        "out/reports", f"slang_migration_{stamp}.json"
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    print(f"[MIGRATION] wrote: {out_path} n_terms={len(items)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
