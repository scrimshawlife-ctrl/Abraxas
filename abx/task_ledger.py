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


def append_event(path: str, ev: Dict[str, Any]) -> None:
    """Generic append-only event writer."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")


def task_event(
    *,
    ledger: str,
    run_id: str,
    task_id: str,
    status: str,
    mode: str,
    claim_id: str = "",
    term: str = "",
    task_kind: str = "",
    detail: str = "",
    artifacts: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Log task execution lifecycle event (STARTED/COMPLETED/BLOCKED).
    Used by WO-77 acquisition executor.
    """
    ev = {
        "kind": "task_event",
        "ts": _utc_now_iso(),
        "run_id": run_id,
        "task_id": task_id,
        "status": status.upper().strip(),  # STARTED/COMPLETED/BLOCKED
        "mode": mode,
        "claim_id": claim_id or None,
        "term": term or None,
        "task_kind": task_kind or None,
        "detail": detail or None,
        "artifacts": artifacts or {},
        "notes": "Append-only task ledger for acquisition loop.",
    }
    append_event(ledger, ev)
    return ev


def task_id(task: Dict[str, Any]) -> str:
    """
    Stable ID based on semantics (not timestamps).
    Used by WO-68 ROI learning.
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
    ap = argparse.ArgumentParser(description="Task ledger writer (supports both WO-68 task_completed and WO-77 task_event)")
    ap.add_argument("--ledger", default="out/ledger/task_ledger.jsonl")
    sub = ap.add_subparsers(dest="cmd")

    # WO-77: task lifecycle events (STARTED/COMPLETED/BLOCKED)
    te = sub.add_parser("task-event", help="Log task execution event (WO-77)")
    te.add_argument("--run-id", required=True)
    te.add_argument("--task-id", required=True)
    te.add_argument("--status", required=True)
    te.add_argument("--mode", required=True)
    te.add_argument("--claim-id", default="")
    te.add_argument("--term", default="")
    te.add_argument("--task-kind", default="")
    te.add_argument("--detail", default="")

    # WO-68: task completion for ROI learning
    tc = sub.add_parser("task-completed", help="Log task completion for ROI learning (WO-68)")
    tc.add_argument("--task-json", required=True, help="Path to a single task dict JSON")
    tc.add_argument("--cost-usd", type=float, default=0.0)
    tc.add_argument("--manual-min", type=int, default=0)
    tc.add_argument("--anchors-added", type=int, default=0)
    tc.add_argument("--domains-added", type=int, default=0)
    tc.add_argument("--fals-tests-added", type=int, default=0)
    tc.add_argument("--after-runs", type=int, default=6, help="How many subsequent runs define after-window")

    args = ap.parse_args()

    if args.cmd == "task-event":
        ev = task_event(
            ledger=args.ledger,
            run_id=args.run_id,
            task_id=args.task_id,
            status=args.status,
            mode=args.mode,
            claim_id=args.claim_id,
            term=args.term,
            task_kind=args.task_kind,
            detail=args.detail,
        )
        print(f"[TASK_LEDGER] {ev['status']} task_id={ev['task_id']}")
        return 0

    if args.cmd == "task-completed":
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

    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
