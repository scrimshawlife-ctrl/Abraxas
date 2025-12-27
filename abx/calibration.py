from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from abx.tpi_forecast import forecast_tpi
from abx.tpi_series import list_tpi_runs


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json(path: str) -> Dict[str, Any]:
    if not path or not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _clamp01(x: float) -> float:
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return float(x)


def mae(y: List[float], yhat: List[float]) -> float:
    n = min(len(y), len(yhat))
    if n <= 0:
        return 0.0
    return sum(abs(float(y[i]) - float(yhat[i])) for i in range(n)) / float(n)


def brier_binary(probs: List[float], events: List[int]) -> float:
    n = min(len(probs), len(events))
    if n <= 0:
        return 0.0
    return sum((float(probs[i]) - float(events[i])) ** 2 for i in range(n)) / float(n)


def calibrate(
    *,
    out_reports: str,
    horizon_steps: int,
    slang_drift_latest: Dict[str, Any],
    scenario_grid: List[Tuple[str, float, float]],
    tau_grid: List[float],
) -> Dict[str, Any]:
    rows = list_tpi_runs(out_reports)
    if len(rows) < (horizon_steps + 3):
        return {
            "version": "calibration.v0.1",
            "ts": _utc_now_iso(),
            "error": "Not enough tpi_*.json runs to calibrate.",
            "n_runs": len(rows),
        }

    rids = [rid for _, rid, _ in rows]
    y = [float(tpi) for _, _, tpi in rows]

    fog_rolls: List[Dict[str, int]] = []
    for rid in rids:
        obj = _read_json(os.path.join(out_reports, f"tpi_{rid}.json"))
        fr = obj.get("fog_roll") if isinstance(obj.get("fog_roll"), dict) else {}
        fog_rolls.append(
            {
                "OP_FOG": int(fr.get("OP_FOG", 0)),
                "FORK_STORM": int(fr.get("FORK_STORM", 0)),
                "PROVENANCE_DROUGHT": int(fr.get("PROVENANCE_DROUGHT", 0)),
            }
        )

    best = None
    results = []

    for scen_name, mri, iri in scenario_grid:
        for tau_h in tau_grid:
            preds_all: List[float] = []
            obs_all: List[float] = []
            red_prob: List[float] = []
            red_event: List[int] = []
            for i in range(0, len(y) - horizon_steps):
                tpi_now = y[i]
                fog = fog_rolls[i]
                f = forecast_tpi(
                    tpi_now=tpi_now,
                    fog_roll=fog,
                    slang_drift_obj=slang_drift_latest,
                    horizon_days=horizon_steps,
                    mri=mri,
                    iri=iri,
                    tau_half_life_days=tau_h,
                    scenario_name=scen_name,
                )
                series = f.get("series") if isinstance(f.get("series"), list) else []
                yhat = [float(pt.get("tpi") or 0.0) for pt in series[:horizon_steps]]
                yobs = [float(y[i + j]) for j in range(1, horizon_steps + 1)]
                preds_all.extend(yhat)
                obs_all.extend(yobs)

                p_red = max(yhat) if yhat else float(tpi_now)
                red_prob.append(_clamp01(p_red))
                red_event.append(1 if max(yobs) >= 0.67 else 0)

            score_mae = mae(obs_all, preds_all)
            score_brier = brier_binary(red_prob, red_event)
            rec = {
                "scenario": scen_name,
                "mri": float(mri),
                "iri": float(iri),
                "tau_half_life_days": float(tau_h),
                "mae": float(score_mae),
                "brier_red_within_horizon": float(score_brier),
            }
            results.append(rec)
            if best is None:
                best = rec
            else:
                if (rec["mae"] < best["mae"] - 1e-9) or (
                    abs(rec["mae"] - best["mae"]) <= 1e-9
                    and rec["brier_red_within_horizon"]
                    < best["brier_red_within_horizon"]
                ):
                    best = rec

    results.sort(
        key=lambda r: (
            float(r["mae"]),
            float(r["brier_red_within_horizon"]),
            r["scenario"],
        )
    )
    return {
        "version": "calibration.v0.1",
        "ts": _utc_now_iso(),
        "out_reports": out_reports,
        "horizon_steps": int(horizon_steps),
        "n_runs": len(rows),
        "best": best,
        "top10": results[:10],
        "notes": (
            "Backtest uses run-to-run steps (not literal days). "
            "Best params minimize MAE then Brier on RED-within-horizon."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Calibrate TPI forecast parameters over historical runs"
    )
    ap.add_argument("--out-reports", default="out/reports")
    ap.add_argument("--horizon-steps", type=int, default=8)
    ap.add_argument(
        "--slang-drift",
        default="",
        help="Path to slang_drift_*.json; if empty uses latest in out/reports",
    )
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    slang = {}
    if args.slang_drift:
        slang = _read_json(args.slang_drift)
    else:
        try:
            import glob

            paths = sorted(glob.glob(os.path.join(args.out_reports, "slang_drift_*.json")))
            slang = _read_json(paths[-1]) if paths else {}
        except Exception:
            slang = {}

    scenario_grid = [
        ("CONSERVATIVE", 0.45, 0.60),
        ("BALANCED", 0.55, 0.55),
        ("AGGRESSIVE", 0.70, 0.45),
        ("RECOVERY", 0.40, 0.75),
    ]
    tau_grid = [7.0, 10.0, 14.0, 21.0, 30.0, 45.0]

    obj = calibrate(
        out_reports=args.out_reports,
        horizon_steps=int(args.horizon_steps),
        slang_drift_latest=slang if isinstance(slang, dict) else {},
        scenario_grid=scenario_grid,
        tau_grid=tau_grid,
    )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = args.out or os.path.join(
        args.out_reports, f"calibration_report_{stamp}.json"
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    print(f"[CALIBRATION] wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
