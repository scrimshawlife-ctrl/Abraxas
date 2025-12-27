from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List

from abx.evidence_ledger import EvidenceLedger


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _write_json(path: str, obj: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def _norm_term(s: str) -> str:
    s = (s or "").strip().lower()
    s = " ".join(s.replace("-", " ").replace("_", " ").split())
    return s


def _profiles(a2: Dict[str, Any]) -> List[Dict[str, Any]]:
    raw = a2.get("raw_full") if isinstance(a2, dict) else {}
    profs = (
        raw.get("profiles")
        if isinstance(raw, dict) and isinstance(raw.get("profiles"), list)
        else None
    )
    if isinstance(profs, list):
        return [p for p in profs if isinstance(p, dict)]
    views = (a2.get("views") or {}).get("profiles_top") if isinstance(a2, dict) else None
    return [p for p in views if isinstance(views, list) and isinstance(p, dict)] if isinstance(views, list) else []


def compute_uplifts_for_run(
    *,
    run_id: str,
    out_reports: str,
    ledger_path: str,
) -> Dict[str, Any]:
    a2_path = os.path.join(out_reports, f"a2_phase_{run_id}.json")
    a2 = _read_json(a2_path)
    profs = _profiles(a2)

    ledger = EvidenceLedger(ledger_path)
    events = ledger.load_all()

    by_term: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for ev in events:
        tk = _norm_term(str(ev.get("term") or ""))
        if tk:
            by_term[tk].append(ev)

    out_terms: Dict[str, Any] = {}
    for profile in profs:
        term = str(profile.get("term") or "").strip()
        if not term:
            continue
        tk = _norm_term(term)
        es = by_term.get(tk, [])

        uniq_sources = set()
        uniq_publishers = set()
        primary_hits = 0
        ff_hits = 0
        weight_sum = 0.0
        high_quality = 0

        for ev in es:
            src = str(ev.get("source") or "")
            if src:
                uniq_sources.add(src)
            pub = str(ev.get("publisher") or "")
            if pub:
                uniq_publishers.add(pub)

            tags = ev.get("tags") if isinstance(ev.get("tags"), list) else []
            w = float(ev.get("weight") or 0.0)
            weight_sum += w

            if (
                "primary" in tags
                or "filing" in tags
                or "transcript" in tags
                or "official" in tags
            ):
                primary_hits += 1
            if "falsification" in tags or "disconfirm" in tags or "test" in tags:
                ff_hits += 1
            if "gov" in tags or "edu" in tags or "sec" in tags or "court" in tags:
                high_quality += 1

        prov = 0.0
        prov += min(0.55, 0.08 * len(uniq_sources))
        prov += min(0.25, 0.06 * len(uniq_publishers))
        prov += min(0.20, 0.05 * weight_sum)
        prov = max(0.0, min(1.0, prov))

        up_att = min(0.35, 0.08 * primary_hits + 0.05 * high_quality)
        up_div = min(0.35, 0.05 * len(uniq_publishers) + 0.03 * len(uniq_sources))
        up_ff = min(0.35, 0.10 * ff_hits)

        out_terms[term] = {
            "provenance_index": float(prov),
            "uplift_attribution": float(up_att),
            "uplift_diversity": float(up_div),
            "ff_support": float(up_ff),
            "counts": {
                "events": len(es),
                "unique_sources": len(uniq_sources),
                "unique_publishers": len(uniq_publishers),
                "primary_hits": primary_hits,
                "ff_hits": ff_hits,
                "high_quality_hits": high_quality,
            },
        }

    return {
        "version": "evidence_uplift.v0.1",
        "ts": _utc_now_iso(),
        "run_id": run_id,
        "ledger_path": ledger_path,
        "terms": out_terms,
        "notes": "Conservative uplift suggestions derived from evidence ledger; apply as additive caps to A2 fields.",
    }


def main() -> int:
    p = argparse.ArgumentParser(
        description="Compute evidence uplift for a run from evidence ledger"
    )
    p.add_argument("--run-id", required=True)
    p.add_argument("--out-reports", default="out/reports")
    p.add_argument("--ledger", default="out/ledger/evidence_ledger.jsonl")
    p.add_argument("--out", default="")
    args = p.parse_args()

    obj = compute_uplifts_for_run(
        run_id=args.run_id,
        out_reports=args.out_reports,
        ledger_path=args.ledger,
    )
    out_path = args.out or os.path.join(
        args.out_reports, f"evidence_uplift_{args.run_id}.json"
    )
    _write_json(out_path, obj)
    print(f"[EVIDENCE_UPLIFT] wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
