from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
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


def _term_stats(cands: List[Dict[str, Any]]) -> Dict[str, Any]:
    scores = [float(c.get("score") or 0.0) for c in cands]
    runs = {str(c.get("oracle_id") or "") for c in cands}
    n_runs = len(runs - {""})
    avg = sum(scores) / len(scores) if scores else 0.0
    peak = max(scores) if scores else 0.0
    half_life = int(max(2, min(90, 4 + 6 * n_runs + 20 * avg)))
    review_every = int(max(1, min(21, 7 if half_life >= 30 else 3)))
    return {
        "n_mentions": len(cands),
        "n_runs": n_runs,
        "avg_score": float(avg),
        "peak_score": float(peak),
        "half_life_days": half_life,
        "review_every_days": review_every,
    }


def promote_terms(
    *,
    run_id: str,
    candidates_ledger: str,
    aalmanac_ledger: str,
    min_mentions: int,
    min_runs: int,
    min_avg_score: float,
    limit: int,
) -> Dict[str, Any]:
    cands = [
        c
        for c in _read_jsonl(candidates_ledger)
        if c.get("kind") == "slang_candidate" and (c.get("status") == "SHADOW")
    ]
    by_term = defaultdict(list)
    for c in cands:
        t = str(c.get("term") or "").strip()
        if t:
            by_term[t].append(c)

    promoted = []
    scored = []
    for term, lst in by_term.items():
        st = _term_stats(lst)
        if st["n_mentions"] < int(min_mentions):
            continue
        if st["n_runs"] < int(min_runs):
            continue
        if float(st["avg_score"]) < float(min_avg_score):
            continue
        scored.append(
            (int(st["n_runs"]), int(st["n_mentions"]), float(st["avg_score"]), term, st)
        )
    scored.sort(key=lambda x: (-x[0], -x[1], -x[2], x[3]))

    for _, _, _, term, st in scored[: int(limit)]:
        entry = {
            "kind": "aalmanac_entry",
            "ts": _utc_now_iso(),
            "run_id": run_id,
            "term": term,
            "tier": "CANON",
            "tau": {
                "half_life_days": st["half_life_days"],
                "review_every_days": st["review_every_days"],
            },
            "stats": st,
            "definition": "",
            "usage": "",
            "motifs": [],
            "provenance": {
                "source": "oracle_runs",
                "promotion_rule": {
                    "min_mentions": min_mentions,
                    "min_runs": min_runs,
                    "min_avg_score": min_avg_score,
                },
            },
            "notes": "Promoted from SHADOW slang_candidate ledger via deterministic governance thresholds. Fill definition/usage later as structured enrichment.",
        }
        _append_jsonl(aalmanac_ledger, entry)
        promoted.append(entry)

    return {"n_candidates": len(cands), "n_promoted": len(promoted), "promoted": promoted}


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Promote slang candidates into AAlmanac (canon) via deterministic rules"
    )
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--candidates", default="out/ledger/slang_candidates.jsonl")
    ap.add_argument("--aalmanac", default="out/ledger/aalmanac.jsonl")
    ap.add_argument("--min-mentions", type=int, default=3)
    ap.add_argument("--min-runs", type=int, default=2)
    ap.add_argument("--min-avg-score", type=float, default=0.55)
    ap.add_argument("--limit", type=int, default=25)
    args = ap.parse_args()

    res = promote_terms(
        run_id=args.run_id,
        candidates_ledger=args.candidates,
        aalmanac_ledger=args.aalmanac,
        min_mentions=int(args.min_mentions),
        min_runs=int(args.min_runs),
        min_avg_score=float(args.min_avg_score),
        limit=int(args.limit),
    )
    print(
        f"[AALMANAC] promoted {res['n_promoted']} (from {res['n_candidates']} candidates)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
