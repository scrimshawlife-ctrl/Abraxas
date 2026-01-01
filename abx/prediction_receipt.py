from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_jsonl(path: str, max_lines: int = 800000) -> List[Dict[str, Any]]:
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
            except Exception:
                continue
            if isinstance(obj, dict):
                out.append(obj)
    return out


def _find_by_pred_id(rows: List[Dict[str, Any]], pred_id: str) -> Dict[str, Any]:
    for row in rows:
        if str(row.get("pred_id") or "") == pred_id:
            return row
    return {}


def main() -> int:
    p = argparse.ArgumentParser(description="Emit prediction receipt card")
    p.add_argument("--pred-id", required=True)
    p.add_argument("--run-id", required=False, default="")
    p.add_argument("--out-reports", default="out/reports")
    p.add_argument("--pred-ledger", default="out/forecast_ledger/predictions.jsonl")
    p.add_argument("--out-ledger", default="out/forecast_ledger/outcomes.jsonl")
    args = p.parse_args()

    ts = _utc_now_iso()
    preds = _read_jsonl(args.pred_ledger)
    outs = _read_jsonl(args.out_ledger)
    pred = _find_by_pred_id(preds, args.pred_id)
    outcome = _find_by_pred_id(outs, args.pred_id)

    out_md = os.path.join(args.out_reports, f"prediction_receipt_{args.pred_id}.md")
    os.makedirs(os.path.dirname(out_md), exist_ok=True)
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("# Prediction Receipt\n\n")
        f.write(f"- pred_id: `{args.pred_id}`\n")
        if args.run_id:
            f.write(f"- run_id: `{args.run_id}`\n")
        f.write(f"- ts: `{ts}`\n\n")

        if not pred:
            f.write("## Prediction\n- not found in predictions ledger\n")
        else:
            f.write("## Prediction\n")
            f.write(f"- term: `{pred.get('term')}`\n")
            f.write(f"- terms: `{pred.get('terms')}`\n")
            f.write(f"- horizon: `{pred.get('horizon')}`\n")
            f.write(f"- p: `{pred.get('p')}`\n")
            f.write(f"- window_end_ts: `{pred.get('window_end_ts')}`\n")
            if pred.get("flags"):
                f.write(f"- flags: `{pred.get('flags')}`\n")
            ctx = pred.get("context") if isinstance(pred.get("context"), dict) else {}
            if ctx:
                dmx = ctx.get("dmx") or {}
                gate = ctx.get("gate") or {}
                gate_inputs = ctx.get("gate_inputs") or {}
                f.write("\n## Context\n")
                if isinstance(dmx, dict):
                    f.write(
                        "- dmx: "
                        f"overall={dmx.get('overall_manipulation_risk')} "
                        f"bucket={dmx.get('bucket')}\n"
                    )
                if isinstance(gate, dict) and gate:
                    f.write(
                        "- gate: "
                        f"horizon_max={gate.get('horizon_max')} "
                        f"eeb_mul={gate.get('eeb_multiplier')} "
                        f"esc={gate.get('evidence_escalation')}\n"
                    )
                    if gate.get("flags"):
                        f.write(f"  - gate_flags: {gate.get('flags')}\n")
                if isinstance(gate_inputs, dict) and gate_inputs:
                    f.write(
                        f"- gate_inputs: terms={gate_inputs.get('terms')} "
                        f"weighted={gate_inputs.get('weighted_metrics')}\n"
                    )

        f.write("\n## Outcome\n")
        if not outcome:
            f.write("- unresolved\n")
        else:
            f.write(f"- result: `{outcome.get('result')}`\n")
            if outcome.get("notes"):
                f.write(f"- notes: {outcome.get('notes')}\n")
            if outcome.get("evidence"):
                f.write(f"- evidence: {outcome.get('evidence')}\n")

    print(f"[PREDICTION_RECEIPT] wrote: {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
