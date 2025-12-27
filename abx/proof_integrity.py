from __future__ import annotations

import argparse
import json
import math
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


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


def _entropy(counter: Counter) -> float:
    total = sum(counter.values())
    if total <= 0:
        return 0.0
    ent = 0.0
    for c in counter.values():
        p = c / total
        ent -= p * math.log(p + 1e-12, 2)
    return float(ent)


def compute_pis(
    *,
    anchor_ledger: str,
    window_runs: int = 14,
    run_order: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    PIS in [0,1].
    Uses last N runs (by run_id order if provided; else by ledger timestamp).
    Penalizes:
      - duplicate URL reuse
      - low domain entropy
      - low primary fraction
    """
    entries = [e for e in _read_jsonl(anchor_ledger) if str(e.get("kind") or "") == "anchor_added"]
    if not entries:
        return {"version": "proof_integrity.v0.1", "ts": _utc_now_iso(), "error": "No anchors found.", "PIS": 0.0}

    # Determine run window
    if run_order:
        last_runs = run_order[-window_runs:] if len(run_order) > window_runs else run_order
        allowed = set(last_runs)
        w = [e for e in entries if str(e.get("run_id") or "") in allowed]
    else:
        entries.sort(key=lambda d: str(d.get("ts") or ""))
        # approximate by tail of entries then derive unique run_ids
        tail = entries[-5000:]  # cap
        run_ids = []
        seen = set()
        for e in reversed(tail):
            rid = str(e.get("run_id") or "")
            if rid and rid not in seen:
                run_ids.append(rid)
                seen.add(rid)
            if len(run_ids) >= window_runs:
                break
        allowed = set(run_ids)
        w = [e for e in entries if str(e.get("run_id") or "") in allowed]

    if not w:
        return {"version": "proof_integrity.v0.1", "ts": _utc_now_iso(), "error": "No anchors in window.", "PIS": 0.0}

    url_hashes = [str(e.get("url_hash") or "") for e in w if e.get("url_hash")]
    domains = [str(e.get("domain") or "") for e in w if e.get("domain")]
    prim = [1 for e in w if bool(e.get("primary"))]

    url_counts = Counter(url_hashes)
    dom_counts = Counter(domains)

    # duplicates: fraction of urls that are repeats
    dup_total = sum(c - 1 for c in url_counts.values() if c > 1)
    denom = max(1, len(url_hashes))
    dup_rate = float(dup_total / denom)

    # domain entropy normalized
    ent = _entropy(dom_counts)
    ent_max = math.log(max(1, len(dom_counts)), 2) if len(dom_counts) > 1 else 0.0
    ent_norm = float(ent / (ent_max + 1e-9)) if ent_max > 0 else 0.0

    # primary ratio
    prim_ratio = float(len(prim) / max(1, len(w)))

    # score assembly
    # - high entropy good, low duplicates good, high primary good
    s_entropy = ent_norm
    s_dup = max(0.0, 1.0 - min(1.0, dup_rate * 2.0))  # punish duplicates aggressively
    s_primary = min(1.0, prim_ratio / 0.35)  # reaching 35% primary is "good"

    pis = float(max(0.0, min(1.0, 0.45 * s_entropy + 0.35 * s_dup + 0.20 * s_primary)))

    return {
        "version": "proof_integrity.v0.1",
        "ts": _utc_now_iso(),
        "window_runs": int(window_runs),
        "n_anchors": len(w),
        "n_urls": len(url_hashes),
        "n_domains": len(dom_counts),
        "dup_rate": dup_rate,
        "domain_entropy_norm": ent_norm,
        "primary_ratio": prim_ratio,
        "components": {"entropy": s_entropy, "dup": s_dup, "primary": s_primary},
        "PIS": pis,
        "notes": "PIS hardens evidence quality and reduces Goodhart risk. Used as a soft multiplier only (no trimming).",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Compute Proof Integrity Score (PIS) from anchor ledger")
    ap.add_argument("--anchor-ledger", default="out/ledger/anchor_ledger.jsonl")
    ap.add_argument("--window-runs", type=int, default=14)
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    obj = compute_pis(anchor_ledger=args.anchor_ledger, window_runs=int(args.window_runs))
    out_path = args.out or os.path.join("out/reports", f"proof_integrity_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    print(f"[PIS] wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
