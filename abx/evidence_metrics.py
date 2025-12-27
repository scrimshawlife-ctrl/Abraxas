from __future__ import annotations

import argparse
import glob
import json
import os
from collections import defaultdict, Counter
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _latest(path: str, pattern: str) -> str:
    paths = sorted(glob.glob(os.path.join(path, pattern)))
    return paths[-1] if paths else ""


def _clamp(x: float, a: float, b: float) -> float:
    return float(max(a, min(b, x)))


def compute_claim_scores(graph: Dict[str, Any], pis: float = 0.0) -> Dict[str, Any]:
    """
    CSS = normalized support score (weighted)
    CPR = contradiction pressure ratio
    SDR = domain drift rate (how often domain flips relation across claims over time)
    """
    edges = graph.get("edges") if isinstance(graph.get("edges"), list) else []

    # claim aggregates
    support = defaultdict(float)
    contra = defaultdict(float)
    prim_support = defaultdict(float)
    dom_support = defaultdict(Counter)  # claim -> domain counts (support only)
    dom_contra = defaultdict(Counter)

    # domain stance history for SDR
    dom_stance_seq = defaultdict(list)  # domain -> list of (+1/-1) in time order (approx by ts)

    for e in edges:
        if not isinstance(e, dict):
            continue
        if e.get("kind") != "ANCHOR_CLAIM":
            continue
        cid = str(e.get("dst") or "")
        rel = str(e.get("relation") or "")
        w = float(e.get("weight") or 1.0)
        primary = bool(e.get("primary"))
        domain = str(e.get("domain") or "")
        ts = str(e.get("ts") or "")

        # soft trust scaling by PIS (does not censor; just weights)
        trust = 0.85 + 0.15 * _clamp(pis, 0.0, 1.0)
        ww = float(w * trust * (1.35 if primary else 1.0))

        if rel == "SUPPORTS" or rel == "ORIGINATES" or rel == "REFRAMES":
            support[cid] += ww
            dom_support[cid][domain] += 1
            if primary:
                prim_support[cid] += ww
            if domain:
                dom_stance_seq[domain].append((ts, +1))
        elif rel == "CONTRADICTS":
            contra[cid] += ww
            dom_contra[cid][domain] += 1
            if domain:
                dom_stance_seq[domain].append((ts, -1))

    claim_scores = {}
    for cid in set(list(support.keys()) + list(contra.keys())):
        s = float(support.get(cid, 0.0))
        c = float(contra.get(cid, 0.0))
        # CPR: contradiction pressure
        cpr = float(c / (s + 1e-9))
        # CSS: support minus contradiction, squashed to [0,1]
        raw = (s - 0.85 * c)
        css = 1.0 / (1.0 + (2.71828 ** (-0.35 * raw)))  # logistic-ish
        # diversity bonus: distinct domains matter
        ds = len([d for d in dom_support[cid].keys() if d])
        dc = len([d for d in dom_contra[cid].keys() if d])
        div = _clamp((ds + 0.5 * dc) / 6.0, 0.0, 1.0)
        css = _clamp(css * (0.85 + 0.15 * div), 0.0, 1.0)
        claim_scores[cid] = {
            "CSS": float(css),
            "CPR": float(cpr),
            "support_w": float(s),
            "contra_w": float(c),
            "primary_support_w": float(prim_support.get(cid, 0.0)),
            "support_domains": int(ds),
            "contra_domains": int(dc),
        }

    # SDR: per domain stance flips across time
    sdr = {}
    for dom, seq in dom_stance_seq.items():
        seq.sort(key=lambda t: t[0])
        flips = 0
        prev = 0
        for _, st in seq:
            if prev != 0 and st != prev:
                flips += 1
            prev = st
        # normalize by opportunities
        denom = max(1, len(seq) - 1)
        sdr[dom] = float(flips / denom)

    return {
        "version": "evidence_metrics.v0.1",
        "ts": _utc_now_iso(),
        "pis_used": float(pis),
        "n_claims_scored": len(claim_scores),
        "claim_scores": claim_scores,
        "SDR": sdr,
        "notes": "CSS/CPR are claim-level. SDR is domain-level drift. All are weightings; nothing is trimmed.",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Compute evidence metrics (CSS/CPR/SDR) from compiled evidence graph")
    ap.add_argument("--graph", default="")
    ap.add_argument("--pis", type=float, default=None)
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    gpath = args.graph
    if not gpath:
        gpath = _latest("out/graphs", "evidence_graph_*.json")
    g = _read_json(gpath) if gpath else {}

    pis = args.pis
    if pis is None:
        pis_path = _latest("out/reports", "proof_integrity_*.json")
        pis_obj = _read_json(pis_path) if pis_path else {}
        pis = float(pis_obj.get("PIS") or 0.0) if isinstance(pis_obj, dict) else 0.0

    obj = compute_claim_scores(g, pis=float(pis))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = args.out or os.path.join("out/reports", f"evidence_metrics_{stamp}.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    print(f"[EVID_METRICS] wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
