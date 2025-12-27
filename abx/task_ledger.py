from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _norm(s: str) -> str:
    s = (s or "").strip().lower()
    s = " ".join(s.replace("-", " ").replace("_", " ").split())
    return s


def task_id(task: Dict[str, Any]) -> str:
    """
    Stable ID based on semantics (not timestamps).
    """
    rid = str(task.get("run_id") or "")
    term = _norm(str(task.get("term") or ""))
    ttype = str(task.get("task_type") or "")
    driver = str(task.get("dominant_driver") or "")
    base = f"{rid}|{term}|{ttype}|{driver}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:20]


def append_task_completed(
    *,
    ledger_path: str,
    task: Dict[str, Any],
    cost: Dict[str, Any],
    evidence: Dict[str, Any],
    result_window: Dict[str, Any],
) -> Dict[str, Any]:
    os.makedirs(os.path.dirname(ledger_path), exist_ok=True)
    ev = {
        "kind": "task_completed",
        "ts": _utc_now_iso(),
        "task_id": task_id(task),
        "run_id": str(task.get("run_id") or ""),
        "term": str(task.get("term") or ""),
        "task_type": str(task.get("task_type") or ""),
        "dominant_driver": str(task.get("dominant_driver") or ""),
        "ml": task.get("ml") if isinstance(task.get("ml"), dict) else {},
        "cost": cost if isinstance(cost, dict) else {},
        "evidence": evidence if isinstance(evidence, dict) else {},
        "result_window": result_window if isinstance(result_window, dict) else {},
        "notes": "User-completed or system-completed acquisition task. Used for ROI learning.",
    }
    with open(ledger_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    return ev


def main() -> int:
    ap = argparse.ArgumentParser(description="Append task_completed event to task ledger")
    ap.add_argument("--ledger", default="out/ledger/task_ledger.jsonl")
    ap.add_argument("--task-json", required=True, help="Path to a single task dict JSON")
    ap.add_argument("--cost-usd", type=float, default=0.0)
    ap.add_argument("--manual-min", type=int, default=0)
    ap.add_argument("--anchors-added", type=int, default=0)
    ap.add_argument("--domains-added", type=int, default=0)
    ap.add_argument("--fals-tests-added", type=int, default=0)
    ap.add_argument("--after-runs", type=int, default=6, help="How many subsequent runs define after-window")
    args = ap.parse_args()

    with open(args.task_json, "r", encoding="utf-8") as f:
        task = json.load(f)
    if not isinstance(task, dict):
        raise SystemExit("task-json must be a JSON object")

    ev = append_task_completed(
        ledger_path=args.ledger,
        task=task,
        cost={"usd": float(args.cost_usd), "manual_min": int(args.manual_min)},
        evidence={"anchors_added": int(args.anchors_added), "domains_added": int(args.domains_added), "fals_tests_added": int(args.fals_tests_added)},
        result_window={"after_runs": int(args.after_runs)},
    )
    print(f"[TASK_LEDGER] appended task_id={ev['task_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
