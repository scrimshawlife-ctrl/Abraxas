from __future__ import annotations

import argparse
import glob
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple


def _read_json(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


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


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _parse_ts(ts: str) -> datetime:
    # expects ISO; fall back to now
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return datetime.now(timezone.utc)


def build_timeseries(
    *,
    truth_map_reports_glob: str = "out/reports/truth_contamination_*.json",
    evidence_graph_ledger: str = "out/ledger/evidence_graph.jsonl",
) -> Dict[str, Any]:
    """
    Collect truth map outputs over time into a per-claim time series.
    truth_contamination reports already contain CS_score/ML_score/quadrant per claim.
    We also enrich with claim_handle/text from evidence_graph ledger if present.
    """
    reports = sorted(glob.glob(truth_map_reports_glob))
    if not reports:
        return {"version": "claim_timeseries.v0.1", "ts": _utc_now_iso(), "error": "No truth_contamination reports found."}

    # claim metadata (handle/text) from ledger
    claim_meta = {}
    for e in _read_jsonl(evidence_graph_ledger):
        if str(e.get("kind") or "") != "claim_added":
            continue
        cid = str(e.get("claim_id") or "")
        if cid and cid not in claim_meta:
            claim_meta[cid] = {
                "term": e.get("term"),
                "claim_handle": e.get("claim_handle"),
                "claim_type": e.get("claim_type"),
                "text": e.get("text"),
            }

    series = {}  # claim_id -> list[point]
    for rp in reports:
        obj = _read_json(rp)
        ts = str(obj.get("ts") or "")
        claims = obj.get("claims") if isinstance(obj.get("claims"), dict) else {}
        for cid, v in claims.items():
            if not isinstance(v, dict):
                continue
            pt = {
                "ts": ts,
                "CS_score": float(v.get("CS_score") or 0.0),
                "ML_score": float(v.get("ML_score") or 0.0),
                "quadrant": str(v.get("quadrant") or ""),
                "inputs": v.get("inputs") if isinstance(v.get("inputs"), dict) else {},
                "source_report": os.path.basename(rp),
            }
            series.setdefault(cid, []).append(pt)

    # sort points by timestamp
    for cid, pts in series.items():
        pts.sort(key=lambda p: _parse_ts(str(p.get("ts") or "")))

    return {
        "version": "claim_timeseries.v0.1",
        "ts": _utc_now_iso(),
        "n_reports": len(reports),
        "n_claims": len(series),
        "claim_meta": claim_meta,
        "series": series,
        "notes": "Per-claim timeline assembled from truth_contamination reports + claim metadata from evidence ledger.",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Build claim time series from truth contamination reports")
    ap.add_argument("--truth-glob", default="out/reports/truth_contamination_*.json")
    ap.add_argument("--evidence-ledger", default="out/ledger/evidence_graph.jsonl")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    obj = build_timeseries(truth_map_reports_glob=args.truth_glob, evidence_graph_ledger=args.evidence_ledger)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = args.out or os.path.join("out/reports", f"claim_timeseries_{stamp}.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    print(f"[CLAIM_TS] wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
