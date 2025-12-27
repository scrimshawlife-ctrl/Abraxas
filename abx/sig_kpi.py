from __future__ import annotations

import argparse
import glob
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

from abx.proof_density import compute_proof_density


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _latest(out_reports: str, pattern: str) -> str:
    paths = sorted(glob.glob(os.path.join(out_reports, pattern)))
    return paths[-1] if paths else ""


def _pick_recent_run_ids(out_reports: str, n: int) -> List[str]:
    paths = sorted(glob.glob(os.path.join(out_reports, "tpi_*.json")))
    rids = [os.path.basename(p).replace("tpi_", "").replace(".json", "") for p in paths]
    return rids[-n:] if len(rids) > n else rids


def _slang_stability(out_reports: str) -> Dict[str, Any]:
    """
    Simple stability: fraction of terms with unchanged canonical+bucket vs previous drift file if present.
    Deterministic, shallow but useful.
    """
    paths = sorted(glob.glob(os.path.join(out_reports, "slang_drift_*.json")))
    if len(paths) < 2:
        return {"available": False, "notes": "Need >=2 slang_drift files"}
    a = _read_json(paths[-2])
    b = _read_json(paths[-1])
    ta = a.get("terms") if isinstance(a.get("terms"), list) else []
    tb = b.get("terms") if isinstance(b.get("terms"), list) else []

    def keymap(ts: List[Dict[str, Any]]) -> Dict[str, str]:
        m = {}
        for it in ts:
            if not isinstance(it, dict):
                continue
            canon = str(it.get("canonical_term") or "").strip().lower()
            if not canon:
                continue
            man = it.get("manufacture") if isinstance(it.get("manufacture"), dict) else {}
            bucket = str(man.get("bucket") or "UNKNOWN")
            m[canon] = bucket
        return m

    ma = keymap(ta)
    mb = keymap(tb)
    common = set(ma.keys()) & set(mb.keys())
    if not common:
        return {"available": True, "common": 0, "stability": 0.0}
    same = sum(1 for k in common if ma[k] == mb[k])
    return {
        "available": True,
        "common": int(len(common)),
        "same_bucket": int(same),
        "stability": float(same / float(len(common))),
        "notes": "Bucket stability across last two slang_drift files.",
    }


def compute_sig(
    *,
    out_reports: str,
    ledger_path: str,
    window_runs: int = 14,
) -> Dict[str, Any]:
    # calibration delta: compare latest two reports if available
    cal_paths = sorted(glob.glob(os.path.join(out_reports, "calibration_report_*.json")))
    cal_latest = _read_json(cal_paths[-1]) if cal_paths else {}
    cal_prev = _read_json(cal_paths[-2]) if len(cal_paths) >= 2 else {}
    best = cal_latest.get("best") if isinstance(cal_latest.get("best"), dict) else {}
    best_prev = cal_prev.get("best") if isinstance(cal_prev.get("best"), dict) else {}

    mae_now = float(best.get("mae") or 0.0)
    mae_prev = float(best_prev.get("mae") or mae_now)
    brier_now = float(best.get("brier_red_within_horizon") or 0.0)
    brier_prev = float(best_prev.get("brier_red_within_horizon") or brier_now)

    # Proof density for recent runs
    run_ids = _pick_recent_run_ids(out_reports, window_runs)
    pd = compute_proof_density(out_reports=out_reports, ledger_path=ledger_path, run_ids=run_ids, tpi_threshold=0.45)

    # Slang stability
    ss = _slang_stability(out_reports)

    # Gains (positive is improvement)
    fsg = {
        "mae_delta": float(mae_prev - mae_now),  # positive is improvement
        "brier_delta": float(brier_prev - brier_now),
        "best_params": best,
    }
    pdg = {
        "avg_primary_anchors_per_term": float(pd.get("avg_primary_anchors_per_term") or 0.0),
        "avg_unique_domains_per_term": float(pd.get("avg_unique_domains_per_term") or 0.0),
        "avg_falsification_tests_per_term": float(pd.get("avg_falsification_tests_per_term") or 0.0),
    }
    sdg = {
        "slang_bucket_stability": float(ss.get("stability") or 0.0) if ss.get("available") else None,
        "notes": ss.get("notes"),
    }
    tcg = {
        "tau_half_life_days": float(best.get("tau_half_life_days") or 0.0),
        "scenario": best.get("scenario"),
    }

    # Optional scalar rollup (bounded, heuristic)
    # Encourage: improved MAE/Brier, higher anchors/diversity, higher stability
    scalar = 0.0
    scalar += 1.8 * max(0.0, fsg["mae_delta"])
    scalar += 1.2 * max(0.0, fsg["brier_delta"])
    scalar += 0.25 * float(pdg["avg_primary_anchors_per_term"])
    scalar += 0.15 * float(pdg["avg_unique_domains_per_term"])
    if sdg["slang_bucket_stability"] is not None:
        scalar += 0.50 * float(sdg["slang_bucket_stability"])
    # squash to 0..1-ish
    scalar = float(min(1.0, max(0.0, scalar)))

    # Proof Integrity soft multiplier (no trimming; just contextual weighting)
    pis_path = _latest(out_reports, "proof_integrity_*.json")
    pis_obj = _read_json(pis_path) if pis_path else {}
    pis = float(pis_obj.get("PIS") or 0.0) if isinstance(pis_obj, dict) else 0.0
    scalar = float(scalar * (0.75 + 0.25 * max(0.0, min(1.0, pis))))

    return {
        "version": "sig_kpi.v0.1",
        "ts": _utc_now_iso(),
        "window_runs": int(window_runs),
        "run_ids": run_ids,
        "FSG": fsg,
        "PDG": pdg,
        "SDG": sdg,
        "TCG": tcg,
        "SIG_scalar": scalar,
        "PIS": {"value": pis, "path": pis_path} if pis_path else {"value": 0.0, "path": None},
        "notes": "SIG is a scoreboard: forecast skill + proof density + signal differentiation + temporal coherence.",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Compute Symbolic Intelligence Gain (SIG) KPI")
    ap.add_argument("--out-reports", default="out/reports")
    ap.add_argument("--ledger", default="out/ledger/evidence_ledger.jsonl")
    ap.add_argument("--window-runs", type=int, default=14)
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    obj = compute_sig(out_reports=args.out_reports, ledger_path=args.ledger, window_runs=int(args.window_runs))
    out_path = args.out or os.path.join(args.out_reports, f"sig_kpi_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    print(f"[SIG] wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
