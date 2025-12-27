from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from abx.evidence_ledger import EvidenceLedger
from abx.media_auth import mav_for_event


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _clamp01(x: float) -> float:
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return float(x)


def _norm_term(s: str) -> str:
    s = (s or "").strip().lower()
    s = " ".join(s.replace("-", " ").replace("_", " ").split())
    return s


def _read_json(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def compute_tpi_for_run(
    *,
    run_id: str,
    out_reports: str,
    ledger_path: str,
    mwr_enriched_path: str = "",
) -> Dict[str, Any]:
    ledger = EvidenceLedger(ledger_path)
    events = ledger.load_all()

    evs = [e for e in events if str(e.get("run_id") or "") == str(run_id)]
    if not evs:
        evs = events[-500:]

    by_term: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for ev in evs:
        t = _norm_term(str(ev.get("term") or ""))
        if not t:
            continue
        if isinstance(ev, dict) and isinstance(ev.get("mav"), dict) and ev.get("mav"):
            mav = ev["mav"]
        else:
            mav = mav_for_event(ev if isinstance(ev, dict) else {})
        by_term[t].append({"event": ev, "mav": mav})

    fog_by_term: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    fog_roll = {"OP_FOG": 0, "FORK_STORM": 0, "PROVENANCE_DROUGHT": 0}
    if mwr_enriched_path and os.path.exists(mwr_enriched_path):
        mwr = _read_json(mwr_enriched_path)
        cw = mwr.get("csp_weather") if isinstance(mwr.get("csp_weather"), dict) else {}
        fi = cw.get("fog_index") if isinstance(cw.get("fog_index"), dict) else {}
        bt = fi.get("by_term") if isinstance(fi.get("by_term"), dict) else {}
        for key, value in bt.items():
            if not isinstance(value, list):
                continue
            tk = _norm_term(str(key))
            for fog in value:
                fog = str(fog)
                fog_by_term[tk][fog] += 1
                if fog in fog_roll:
                    fog_roll[fog] += 1

    def comp_from_list(lst: List[Dict[str, Any]], tk: str) -> Tuple[float, Dict[str, Any]]:
        if not lst:
            base = 0.58
            f = fog_by_term.get(tk, {})
            fp = (
                0.08 * float(f.get("OP_FOG", 0) > 0)
                + 0.06 * float(f.get("FORK_STORM", 0) > 0)
                + 0.06 * float(f.get("PROVENANCE_DROUGHT", 0) > 0)
            )
            return _clamp01(base + fp), {"no_evidence": True, "fog": dict(f)}

        syns = [float(x["mav"]["synthetic_likelihood"]) for x in lst]
        provs = [float(x["mav"]["provenance_integrity"]) for x in lst]
        tpls = [float(x["mav"]["template_reuse_risk"]) for x in lst]

        syn = sum(syns) / max(1, len(syns))
        prov = sum(provs) / max(1, len(provs))
        tpl = sum(tpls) / max(1, len(tpls))

        f = fog_by_term.get(tk, {})
        fogp = 0.0
        fogp += 0.12 * float(f.get("OP_FOG", 0) > 0)
        fogp += 0.10 * float(f.get("FORK_STORM", 0) > 0)
        fogp += 0.10 * float(f.get("PROVENANCE_DROUGHT", 0) > 0)

        tpi = 0.0
        tpi += 0.42 * _clamp01(syn)
        tpi += 0.34 * _clamp01(1.0 - prov)
        tpi += 0.18 * _clamp01(tpl)
        tpi += 0.06 * _clamp01(fogp)

        return _clamp01(tpi), {
            "synthetic_density": float(syn),
            "provenance_integrity_mean": float(prov),
            "template_pressure": float(tpl),
            "fog_flags": {k: int(v) for k, v in f.items()},
            "events": len(lst),
        }

    per_term = {}
    for tk, lst in by_term.items():
        tpi, rec = comp_from_list(lst, tk)
        per_term[tk] = {"tpi": float(tpi), "components": rec}

    if per_term:
        run_tpi = sum(float(v["tpi"]) for v in per_term.values()) / float(
            len(per_term)
        )
    else:
        fogp = 0.0
        fogp += 0.12 * float(fog_roll.get("OP_FOG", 0) > 0)
        fogp += 0.10 * float(fog_roll.get("FORK_STORM", 0) > 0)
        fogp += 0.10 * float(fog_roll.get("PROVENANCE_DROUGHT", 0) > 0)
        run_tpi = _clamp01(0.55 + fogp)

    return {
        "version": "tpi.v0.1",
        "ts": _utc_now_iso(),
        "run_id": run_id,
        "ledger_path": ledger_path,
        "mwr_enriched_path": mwr_enriched_path,
        "run_tpi": float(_clamp01(run_tpi)),
        "fog_roll": fog_roll,
        "per_term": per_term,
        "notes": "TPI measures media pollution conditions (synthetic density + provenance weakness + template pressure + fog flags).",
    }


def _write_json(path: str, obj: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def main() -> int:
    import argparse

    p = argparse.ArgumentParser(description="Compute Truth Pollution Index (TPI) for a run")
    p.add_argument("--run-id", required=True)
    p.add_argument("--out-reports", default="out/reports")
    p.add_argument("--ledger", default="out/ledger/evidence_ledger.jsonl")
    p.add_argument("--out", default="")
    args = p.parse_args()

    mwr_en = os.path.join(args.out_reports, f"mwr_enriched_{args.run_id}.json")
    obj = compute_tpi_for_run(
        run_id=args.run_id,
        out_reports=args.out_reports,
        ledger_path=args.ledger,
        mwr_enriched_path=mwr_en,
    )
    out_path = args.out or os.path.join(args.out_reports, f"tpi_{args.run_id}.json")
    _write_json(out_path, obj)
    print(f"[TPI] wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
