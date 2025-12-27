from __future__ import annotations

import argparse
import glob
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional


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


def build_snapshot(out_reports: str) -> Dict[str, Any]:
    sig_path = _latest(out_reports, "sig_kpi_*.json")
    cal_path = _latest(out_reports, "calibration_report_*.json")
    roi_path = _latest(out_reports, "signal_roi_plan_*.json")

    sig = _read_json(sig_path) if sig_path else {}
    cal = _read_json(cal_path) if cal_path else {}
    best = cal.get("best") if isinstance(cal.get("best"), dict) else {}

    # core values
    fsg = sig.get("FSG") if isinstance(sig.get("FSG"), dict) else {}
    pdg = sig.get("PDG") if isinstance(sig.get("PDG"), dict) else {}
    sdg = sig.get("SDG") if isinstance(sig.get("SDG"), dict) else {}
    tcg = sig.get("TCG") if isinstance(sig.get("TCG"), dict) else {}

    snapshot = {
        "kind": "sig_snapshot",
        "ts": _utc_now_iso(),
        "out_reports": out_reports,
        "pointers": {
            "sig_kpi": sig_path,
            "calibration_report": cal_path,
            "signal_roi_plan": roi_path,
        },
        "SIG_scalar": float(sig.get("SIG_scalar") or 0.0),
        "FSG": {
            "mae_delta": float(fsg.get("mae_delta") or 0.0),
            "brier_delta": float(fsg.get("brier_delta") or 0.0),
        },
        "CAL": {
            "mae": float(best.get("mae") or 0.0),
            "brier_red_within_horizon": float(best.get("brier_red_within_horizon") or 0.0),
            "scenario": best.get("scenario"),
            "tau_half_life_days": float(best.get("tau_half_life_days") or 0.0),
        },
        "PDG": {
            "avg_primary_anchors_per_term": float(pdg.get("avg_primary_anchors_per_term") or 0.0),
            "avg_unique_domains_per_term": float(pdg.get("avg_unique_domains_per_term") or 0.0),
            "avg_falsification_tests_per_term": float(pdg.get("avg_falsification_tests_per_term") or 0.0),
        },
        "SDG": {
            "slang_bucket_stability": sdg.get("slang_bucket_stability"),
            "notes": sdg.get("notes"),
        },
        "TCG": {
            "tau_half_life_days": float(tcg.get("tau_half_life_days") or 0.0),
            "scenario": tcg.get("scenario"),
        },
        "notes": "Snapshot for outcome attribution. Append-only. No censorship.",
    }
    return snapshot


def append_snapshot(ledger_path: str, snap: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(ledger_path), exist_ok=True)
    with open(ledger_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(snap, ensure_ascii=False) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(description="Append SIG snapshot to ledger for outcome attribution")
    ap.add_argument("--out-reports", default="out/reports")
    ap.add_argument("--ledger", default="out/ledger/sig_snapshots.jsonl")
    args = ap.parse_args()

    snap = build_snapshot(args.out_reports)
    append_snapshot(args.ledger, snap)
    print(f"[SIG_SNAPSHOT] appended ts={snap['ts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
