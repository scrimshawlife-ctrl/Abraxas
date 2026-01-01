from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from abx.horizon import bands_index, next_review


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _append_jsonl(path: str, obj: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def emit_forecast(
    *,
    ledger: str,
    run_id: str,
    forecast_id: str,
    title: str,
    horizon_key: str,
    p: float,
    triggers: List[Dict[str, Any]],
    decay_notes: str,
    provenance: Dict[str, Any],
    tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    mods = (
        provenance.get("modulators")
        if isinstance(provenance.get("modulators"), dict)
        else {}
    )
    mri_mult = float(mods.get("MRI_mult", 1.0))
    mri_mult = max(0.25, min(1.0, mri_mult))
    p_eff = float(max(0.0, min(1.0, p * mri_mult)))
    b = bands_index()[horizon_key]
    ts = _utc_now_iso()
    obj = {
        "kind": "forecast",
        "ts": ts,
        "run_id": run_id,
        "forecast_id": forecast_id,
        "title": title,
        "horizon": {
            "key": b.key,
            "days": b.days,
            "half_life_days": b.half_life_days,
            "reevaluate_every_days": b.reevaluate_every_days,
        },
        "p": float(max(0.0, min(1.0, p_eff))),
        "p_raw": float(max(0.0, min(1.0, p))),
        "triggers": triggers,
        "decay_notes": decay_notes,
        "next_review_ts": next_review(ts, b.key),
        "provenance": provenance,
        "tags": tags or [],
        "notes": "Forecast is a probability band with explicit triggers; not a point claim.",
    }
    _append_jsonl(ledger, obj)
    return obj


def main() -> int:
    ap = argparse.ArgumentParser(description="Append to forecast ledger")
    ap.add_argument("--ledger", default="out/ledger/forecast_ledger.jsonl")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--forecast-id", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--horizon", required=True, choices=list(bands_index().keys()))
    ap.add_argument("--p", type=float, required=True)
    ap.add_argument("--triggers-json", default="[]")
    ap.add_argument("--decay-notes", default="")
    ap.add_argument("--prov-json", default="{}")
    ap.add_argument("--tags", default="")
    args = ap.parse_args()

    triggers = json.loads(args.triggers_json)
    prov = json.loads(args.prov_json)
    tags = [t.strip() for t in (args.tags or "").split(",") if t.strip()]

    obj = emit_forecast(
        ledger=args.ledger,
        run_id=args.run_id,
        forecast_id=args.forecast_id,
        title=args.title,
        horizon_key=args.horizon,
        p=float(args.p),
        triggers=triggers if isinstance(triggers, list) else [],
        decay_notes=args.decay_notes,
        provenance=prov if isinstance(prov, dict) else {},
        tags=tags,
    )
    print(
        f"[FORECAST] appended {obj['forecast_id']} horizon={obj['horizon']['key']} p={obj['p']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
