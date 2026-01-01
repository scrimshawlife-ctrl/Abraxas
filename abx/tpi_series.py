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
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def list_tpi_runs(out_reports: str) -> List[Tuple[float, str, float]]:
    paths = sorted(glob.glob(os.path.join(out_reports, "tpi_*.json")))
    rows: List[Tuple[float, str, float]] = []
    for path in paths:
        rid = os.path.basename(path).replace("tpi_", "").replace(".json", "")
        try:
            mt = os.path.getmtime(path)
        except Exception:
            mt = 0.0
        obj = _read_json(path)
        tpi = float(obj.get("run_tpi") or 0.0)
        rows.append((float(mt), str(rid), float(tpi)))
    rows.sort(key=lambda x: (x[0], x[1]))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Build canonical time series of run_tpi across all runs"
    )
    ap.add_argument("--out-reports", default="out/reports")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    rows = list_tpi_runs(args.out_reports)
    series = [
        {"t": float(mt), "run_id": rid, "run_tpi": float(tpi)}
        for mt, rid, tpi in rows
    ]
    obj = {
        "version": "tpi_series.v0.1",
        "ts": _utc_now_iso(),
        "out_reports": args.out_reports,
        "n": len(series),
        "series": series,
        "notes": "Series uses file mtime as time axis (deterministic per filesystem).",
    }
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = args.out or os.path.join(args.out_reports, f"tpi_series_{stamp}.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    print(f"[TPI_SERIES] wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
