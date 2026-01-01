from __future__ import annotations

import argparse
import glob
import json
import os
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


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


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Generate mimetic weather report from AAlmanac + candidates + optional risk/deficits"
    )
    ap.add_argument("--aalmanac", default="out/ledger/aalmanac.jsonl")
    ap.add_argument("--candidates", default="out/ledger/slang_candidates.jsonl")
    ap.add_argument("--truth-pollution", default="")
    ap.add_argument("--deficits", default="")
    ap.add_argument("--out", default="")
    ap.add_argument("--recent-n", type=int, default=400)
    ap.add_argument("--migration", default="")
    args = ap.parse_args()

    if not args.truth_pollution:
        tp = sorted(glob.glob("out/reports/truth_pollution_*.json"))
        args.truth_pollution = tp[-1] if tp else ""
    if not args.deficits:
        dp = sorted(glob.glob("out/reports/deficits_*.json"))
        args.deficits = dp[-1] if dp else ""

    if not args.migration:
        mp = sorted(glob.glob("out/reports/slang_migration_*.json"))
        args.migration = mp[-1] if mp else ""

    tpv = _read_json(args.truth_pollution) if args.truth_pollution else {}
    deficits = _read_json(args.deficits) if args.deficits else {}
    migration = _read_json(args.migration) if args.migration else {}

    canon = [
        e
        for e in _read_jsonl(args.aalmanac)
        if e.get("kind") == "aalmanac_entry" and e.get("tier") == "CANON"
    ]
    cands = [c for c in _read_jsonl(args.candidates) if c.get("kind") == "slang_candidate"]
    cands = cands[-int(args.recent_n) :]

    cand_counts = Counter(str(c.get("term") or "") for c in cands if c.get("term"))
    top_new = [t for (t, _) in cand_counts.most_common(25)]

    canon_terms = set(str(e.get("term") or "") for e in canon if e.get("term"))
    canon_pressure = [t for t in top_new if t in canon_terms]
    newborn = [t for t in top_new if t not in canon_terms]

    tpv_claims = tpv.get("claims") if isinstance(tpv.get("claims"), dict) else {}
    tpv_vals = [
        float(v.get("TPV") or 0.0)
        for v in tpv_claims.values()
        if isinstance(v, dict)
    ]
    tpv_avg = sum(tpv_vals) / len(tpv_vals) if tpv_vals else 0.0

    def_claims = deficits.get("claims") if isinstance(deficits.get("claims"), dict) else {}
    unstable_n = sum(
        1 for v in def_claims.values() if isinstance(v, dict) and v.get("unstable")
    )
    polluted_n = sum(
        1 for v in def_claims.values() if isinstance(v, dict) and v.get("polluted")
    )

    fronts = []
    if tpv_avg >= 0.55 or polluted_n > 0:
        fronts.append(
            {
                "front": "POLLUTION",
                "severity": float(min(1.0, tpv_avg)),
                "signals": {"tpv_avg": tpv_avg, "polluted_claims": polluted_n},
            }
        )
    if unstable_n > 0:
        fronts.append(
            {
                "front": "DRIFT",
                "severity": float(min(1.0, unstable_n / 20.0)),
                "signals": {"unstable_claims": unstable_n},
            }
        )
    if newborn:
        fronts.append(
            {
                "front": "NEWBORN",
                "severity": float(min(1.0, len(newborn) / 25.0)),
                "terms": newborn[:20],
            }
        )
    if canon_pressure:
        fronts.append(
            {
                "front": "AMPLIFY",
                "severity": float(min(1.0, len(canon_pressure) / 25.0)),
                "terms": canon_pressure[:20],
            }
        )
    mig_top = migration.get("top") if isinstance(migration.get("top"), list) else []
    if mig_top:
        hot = [
            x
            for x in mig_top[:40]
            if float((x or {}).get("migration_score") or 0.0) >= 0.55
        ]
        if hot:
            fronts.append(
                {
                    "front": "MIGRATION",
                    "severity": float(min(1.0, len(hot) / 25.0)),
                    "terms": [x.get("term") for x in hot[:20]],
                    "signals": {"source": args.migration},
                }
            )

    obj = {
        "version": "mimetic_weather.v0.1",
        "ts": _utc_now_iso(),
        "summary": {
            "tpv_avg": float(tpv_avg),
            "unstable_claims": int(unstable_n),
            "polluted_claims": int(polluted_n),
            "n_canon_terms": len(canon_terms),
            "n_recent_candidates": len(cands),
        },
        "fronts": fronts,
        "top_recent_terms": top_new[:50],
        "notes": "Weather is a derived view of symbolic pressure fronts; not a moral judgment. Use it to drive acquisition + AAlmanac promotion.",
    }

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = args.out or os.path.join(
        "out/reports", f"mimetic_weather_{stamp}.json"
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    print(f"[WEATHER] wrote: {out_path} fronts={len(fronts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
