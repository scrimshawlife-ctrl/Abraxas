from __future__ import annotations

import argparse
import json
import math
import os
from datetime import datetime, timezone
from typing import Any, Dict, List


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _clamp01(x: float) -> float:
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return float(x)


def _read_json(path: str) -> Dict[str, Any]:
    if not path or not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _sigmoid(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def _alpha_from_tau_half_life_days(tau_half_life_days: float) -> float:
    half_life = max(0.5, float(tau_half_life_days))
    return float(math.exp(math.log(0.5) / half_life))


def _fog_delta(fog_roll: Dict[str, int]) -> float:
    if not isinstance(fog_roll, dict) or not fog_roll:
        return 0.0
    op = float(fog_roll.get("OP_FOG", 0))
    fs = float(fog_roll.get("FORK_STORM", 0))
    pd = float(fog_roll.get("PROVENANCE_DROUGHT", 0))
    d = 0.0
    d += 0.10 * (1.0 if op > 0 else 0.0)
    d += 0.08 * (1.0 if fs > 0 else 0.0)
    d += 0.07 * (1.0 if pd > 0 else 0.0)
    return float(d)


def _shock_delta(*, slang_drift_obj: Dict[str, Any], ml_threshold: float = 0.67) -> float:
    terms = (
        slang_drift_obj.get("terms")
        if isinstance(slang_drift_obj.get("terms"), list)
        else []
    )
    if not terms:
        return 0.0
    score = 0.0
    n = 0
    for it in terms[:80]:
        if not isinstance(it, dict):
            continue
        nov = it.get("novelty") if isinstance(it.get("novelty"), dict) else {}
        m = it.get("manufacture") if isinstance(it.get("manufacture"), dict) else {}
        d = it.get("drift") if isinstance(it.get("drift"), dict) else {}
        if not bool(nov.get("new_to_window")):
            continue
        ml = float(m.get("ml_score") or 0.0)
        drift = float(d.get("drift_score") or 0.0)
        if ml >= ml_threshold and drift >= 0.45:
            score += (0.6 * ml + 0.4 * drift)
            n += 1
    if n == 0:
        return 0.0
    shock = min(0.25, 0.06 + 0.05 * min(4, n) + 0.03 * (score / float(n)))
    return float(shock)


def forecast_tpi(
    *,
    tpi_now: float,
    fog_roll: Dict[str, int],
    slang_drift_obj: Dict[str, Any],
    horizon_days: int,
    mri: float,
    iri: float,
    tau_half_life_days: float,
    scenario_name: str,
) -> Dict[str, Any]:
    tpi_now = _clamp01(float(tpi_now))
    mri = _clamp01(float(mri))
    iri = _clamp01(float(iri))
    alpha = _alpha_from_tau_half_life_days(float(tau_half_life_days))

    fog_d = _fog_delta(fog_roll)
    shock_d = _shock_delta(slang_drift_obj=slang_drift_obj)

    drive = (mri - iri) * 3.0
    bias = (fog_d * 2.4) + (shock_d * 3.0)

    xs: List[Dict[str, Any]] = []
    cur = tpi_now
    for day in range(1, int(horizon_days) + 1):
        target = _sigmoid(drive + bias)
        nxt = _clamp01(alpha * cur + (1.0 - alpha) * target)
        xs.append({"day": day, "tpi": float(nxt)})
        cur = nxt

    return {
        "scenario": scenario_name,
        "params": {
            "mri": float(mri),
            "iri": float(iri),
            "tau_half_life_days": float(tau_half_life_days),
            "alpha": float(alpha),
            "fog_delta": float(fog_d),
            "shock_delta": float(shock_d),
            "drive": float(drive),
            "bias": float(bias),
        },
        "series": xs,
        "end": float(xs[-1]["tpi"]) if xs else float(tpi_now),
    }


def compute_alerts(series: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    alerts: List[Dict[str, Any]] = []
    if not series:
        return alerts

    def lvl(x: float) -> str:
        if x < 0.34:
            return "GREEN"
        if x < 0.67:
            return "AMBER"
        return "RED"

    prev = float(series[0]["tpi"])
    prev_lvl = lvl(prev)
    for i in range(1, len(series)):
        cur = float(series[i]["tpi"])
        cur_lvl = lvl(cur)
        if cur_lvl != prev_lvl:
            alerts.append(
                {
                    "day": int(series[i]["day"]),
                    "type": "THRESHOLD_CROSS",
                    "from": prev_lvl,
                    "to": cur_lvl,
                    "tpi": float(cur),
                }
            )
        if i >= 6:
            d7 = cur - float(series[i - 6]["tpi"])
            if d7 >= 0.10:
                alerts.append(
                    {
                        "day": int(series[i]["day"]),
                        "type": "ACCEL_7D",
                        "delta": float(d7),
                        "tpi": float(cur),
                    }
                )
        prev, prev_lvl = cur, cur_lvl
    return alerts


def main() -> int:
    p = argparse.ArgumentParser(
        description="Forecast Truth Pollution Index (TPI) over time with MRI/IRI/tau scenarios"
    )
    p.add_argument("--run-id", required=True)
    p.add_argument("--out-reports", default="out/reports")
    p.add_argument(
        "--tpi",
        default="",
        help="Path to tpi_<run_id>.json; if empty, tries out/reports/tpi_<run_id>.json",
    )
    p.add_argument(
        "--slang-drift",
        default="",
        help="Path to slang_drift_*.json; if empty, tries latest in out/reports",
    )
    p.add_argument("--horizon-days", type=int, default=90)
    p.add_argument("--out", default="")
    args = p.parse_args()

    tpi_path = args.tpi or os.path.join(args.out_reports, f"tpi_{args.run_id}.json")
    tpi_obj = _read_json(tpi_path)
    tpi_now = float(tpi_obj.get("run_tpi") or 0.0)
    fog_roll = (
        tpi_obj.get("fog_roll") if isinstance(tpi_obj.get("fog_roll"), dict) else {}
    )

    slang_obj = {}
    if args.slang_drift:
        slang_obj = _read_json(args.slang_drift)
    else:
        try:
            import glob

            paths = sorted(glob.glob(os.path.join(args.out_reports, "slang_drift_*.json")))
            slang_obj = _read_json(paths[-1]) if paths else {}
        except Exception:
            slang_obj = {}

    scenarios = [
        ("CONSERVATIVE", 0.45, 0.60, 14.0),
        ("BALANCED", 0.55, 0.55, 21.0),
        ("AGGRESSIVE", 0.70, 0.45, 30.0),
        ("RECOVERY", 0.40, 0.75, 10.0),
    ]

    forecasts = []
    for name, mri, iri, tau_h in scenarios:
        f = forecast_tpi(
            tpi_now=tpi_now,
            fog_roll=fog_roll,
            slang_drift_obj=slang_obj if isinstance(slang_obj, dict) else {},
            horizon_days=int(args.horizon_days),
            mri=float(mri),
            iri=float(iri),
            tau_half_life_days=float(tau_h),
            scenario_name=name,
        )
        f["alerts"] = compute_alerts(f["series"])
        forecasts.append(f)

    out_obj = {
        "version": "tpi_forecast.v0.1",
        "ts": _utc_now_iso(),
        "run_id": args.run_id,
        "inputs": {
            "tpi_path": tpi_path,
            "slang_drift_path": args.slang_drift or "(latest)",
            "tpi_now": float(tpi_now),
        },
        "horizon_days": int(args.horizon_days),
        "forecasts": forecasts,
        "notes": "Forecast predicts pollution conditions (not truth). Scenarios differ by MRI/IRI/tau memory.",
    }

    out_path = args.out or os.path.join(
        args.out_reports, f"tpi_forecast_{args.run_id}.json"
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_obj, f, ensure_ascii=False, indent=2)
    print(f"[TPI_FORECAST] wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
