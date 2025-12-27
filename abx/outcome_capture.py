from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, List


def _parse_dt(s: str) -> datetime:
    dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


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


def _outs_index(outcomes_rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    idx: Dict[str, Dict[str, Any]] = {}
    for row in outcomes_rows:
        pred_id = row.get("pred_id")
        if pred_id:
            idx[str(pred_id)] = row
    return idx


def due_predictions(
    preds: List[Dict[str, Any]],
    outs_idx: Dict[str, Dict[str, Any]],
    now_iso: str,
    limit: int,
) -> List[Dict[str, Any]]:
    now = _parse_dt(now_iso)
    due: List[Dict[str, Any]] = []
    for pred in preds:
        pred_id = pred.get("pred_id")
        if not pred_id:
            continue
        if str(pred_id) in outs_idx:
            continue
        window_end = pred.get("window_end_ts")
        if not window_end:
            continue
        try:
            end_dt = _parse_dt(str(window_end))
        except Exception:
            continue
        if end_dt <= now:
            due.append(pred)
    due.sort(key=lambda x: str(x.get("window_end_ts") or ""))
    return due[:limit]


def main() -> int:
    p = argparse.ArgumentParser(description="Outcome capture (fast human loop)")
    p.add_argument("--run-id", required=True, help="run id for this capture session")
    p.add_argument("--pred-ledger", default="out/forecast_ledger/predictions.jsonl")
    p.add_argument("--out-ledger", default="out/forecast_ledger/outcomes.jsonl")
    p.add_argument("--limit", type=int, default=25)
    p.add_argument("--now", default=None, help="ISO timestamp (UTC)")
    p.add_argument("--auto-audit", action="store_true")
    p.add_argument("--audit-since", default=None, help="ISO start time filter for audit")
    args = p.parse_args()

    now_iso = args.now or _utc_now_iso()
    preds = _read_jsonl(args.pred_ledger)
    outs = _read_jsonl(args.out_ledger)
    idx = _outs_index(outs)

    due = due_predictions(preds, idx, now_iso=now_iso, limit=int(args.limit))
    if not due:
        print("[OUTCOME_CAPTURE] no due predictions.")
        return 0

    print(f"[OUTCOME_CAPTURE] due={len(due)} now={now_iso}")
    for i, pred in enumerate(due, 1):
        pred_id = pred.get("pred_id")
        term = pred.get("term")
        horizon = pred.get("horizon")
        prob = pred.get("p")
        window_end = pred.get("window_end_ts")
        print(f"\n[{i}/{len(due)}] pred_id={pred_id}")
        print(f" term: {term}")
        print(f" horizon: {horizon}  p={prob}  window_end={window_end}")

        while True:
            res = input(" result (hit/miss/partial/skip/quit): ").strip().lower()
            if res in ("hit", "miss", "partial", "skip", "quit"):
                break
        if res == "quit":
            break
        if res == "skip":
            continue
        notes = input(" notes (optional): ").strip()
        ev = input(" evidence url(s), comma-separated (optional): ").strip()
        evidence: List[Dict[str, Any]] = []
        if ev:
            for url in [x.strip() for x in ev.split(",") if x.strip()]:
                evidence.append({"url": url})

        cmd = [
            "python",
            "-m",
            "abx.forecast_outcome",
            "--run-id",
            args.run_id,
            "--pred-id",
            str(pred_id),
            "--result",
            res,
            "--notes",
            notes,
            "--out-ledger",
            args.out_ledger,
        ]
        if evidence:
            os.makedirs("out/reports", exist_ok=True)
            tmp = f"out/reports/evidence_{args.run_id}_{pred_id}.json"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(evidence, f, ensure_ascii=False, indent=2)
            cmd.extend(["--evidence-json", tmp])

        subprocess.check_call(cmd)

    if args.auto_audit:
        audit_cmd = ["python", "-m", "abx.forecast_audit", "--run-id", f"AUDIT_{args.run_id}"]
        if args.audit_since:
            audit_cmd.extend(["--since", args.audit_since])
        subprocess.check_call(audit_cmd)
        print("[OUTCOME_CAPTURE] audit complete.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
