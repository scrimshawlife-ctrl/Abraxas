from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from abraxas.forecast.scoring import brier_score


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else {}


def _read_jsonl(path: str, max_lines: int = 500000) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    out: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= max_lines:
                break
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    out.append(obj)
            except Exception:
                continue
    return out


def _pollution_bucket(value: float) -> str:
    if value >= 0.70:
        return "HIGH"
    if value >= 0.40:
        return "MED"
    return "LOW"


def main() -> int:
    p = argparse.ArgumentParser(description="Emit scoreboard markdown for a run")
    p.add_argument("--run-id", required=True)
    p.add_argument("--out-reports", default="out/reports")
    p.add_argument("--pred-ledger", default="out/forecast_ledger/predictions.jsonl")
    p.add_argument("--out-ledger", default="out/forecast_ledger/outcomes.jsonl")
    p.add_argument("--mwr", default=None, help="mwr_<run>.json path (for DMX context)")
    p.add_argument("--out-md", default=None)
    args = p.parse_args()

    ts = _utc_now_iso()
    preds = _read_jsonl(args.pred_ledger)
    outs = _read_jsonl(args.out_ledger)
    outs_by = {str(o.get("pred_id")): o for o in outs if o.get("pred_id")}

    resolved = 0
    open_ = 0
    due = 0
    by_horizon: Dict[str, Tuple[List[float], List[int]]] = {}

    now = datetime.now(timezone.utc)
    for pred in preds:
        pred_id = pred.get("pred_id")
        if not pred_id:
            continue
        window_end = pred.get("window_end_ts")
        prob = float(pred.get("p") or 0.5)
        horizon = str(pred.get("horizon") or "weeks")

        if str(pred_id) in outs_by:
            resolved += 1
            res = str(outs_by[str(pred_id)].get("result") or "")
            y = 1 if res == "hit" else 0
            by_horizon.setdefault(horizon, ([], []))[0].append(prob)
            by_horizon.setdefault(horizon, ([], []))[1].append(y)
        else:
            open_ += 1
            if window_end:
                try:
                    end = datetime.fromisoformat(str(window_end).replace("Z", "+00:00"))
                    if end.tzinfo is None:
                        end = end.replace(tzinfo=timezone.utc)
                    if end <= now:
                        due += 1
                except Exception:
                    pass

    calibration = []
    for horizon, (pp, yy) in sorted(by_horizon.items(), key=lambda kv: kv[0]):
        calibration.append((horizon, len(pp), brier_score(pp, yy)))

    mwr_path = args.mwr or os.path.join(args.out_reports, f"mwr_{args.run_id}.json")
    mwr = _read_json(mwr_path)
    dmx = (mwr.get("dmx") or {}) if isinstance(mwr, dict) else {}
    dmx_overall = float(dmx.get("overall_manipulation_risk") or 0.0)
    bucket = _pollution_bucket(dmx_overall)

    out_md = args.out_md or os.path.join(
        args.out_reports, f"scoreboard_{args.run_id}.md"
    )
    os.makedirs(os.path.dirname(out_md), exist_ok=True)
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("# Abraxas Scoreboard\n\n")
        f.write(f"- run_id: `{args.run_id}`\n")
        f.write(f"- ts: `{ts}`\n\n")
        f.write("## Status\n")
        f.write(f"- resolved: **{resolved}**\n")
        f.write(f"- open: **{open_}**\n")
        f.write(f"- due (needs outcome): **{due}**\n\n")
        f.write("## Pollution Context (MWR DMX)\n")
        f.write(f"- overall_manipulation_risk: **{dmx_overall:.3f}**\n")
        f.write(f"- bucket: **{bucket}**\n\n")
        f.write("## Calibration (Brier by horizon; resolved only)\n")
        if not calibration:
            f.write("- (no resolved predictions yet)\n")
        else:
            for horizon, count, brier in calibration:
                f.write(f"- {horizon}: n={count}  brier={brier:.3f}\n")
        f.write("\n")

    print(f"[SCOREBOARD] wrote: {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
