from __future__ import annotations

import argparse
import glob
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

from abx.capabilities import detect_capabilities
from abx.task_ledger import task_event


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _latest(dir_path: str, pattern: str) -> str:
    paths = sorted(glob.glob(os.path.join(dir_path, pattern)))
    return paths[-1] if paths else ""


def _read_json(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _write_json(path: str, obj: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def _offline_packet(task: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "kind": "offline_acquisition_packet",
        "ts": _utc_now_iso(),
        "task_id": task.get("task_id"),
        "claim_id": task.get("claim_id"),
        "term": task.get("term"),
        "task_kind": task.get("task_kind"),
        "title": task.get("title"),
        "why": task.get("why"),
        "steps": task.get("steps"),
        "inputs_needed": [
            "Any relevant screenshots/links/files",
            "User notes (observations, first-seen timestamps)",
            "Any primary documents if available",
        ],
        "notes": "This packet exists because online execution was blocked or not available.",
    }


def execute_plan(
    *,
    plan_path: str,
    run_id: str,
    ledger_path: str = "out/ledger/task_ledger.jsonl",
    max_tasks: int = 10,
) -> Dict[str, Any]:
    caps = detect_capabilities()
    plan = _read_json(plan_path)
    tasks = plan.get("tasks") if isinstance(plan.get("tasks"), list) else []
    tasks = tasks[:max_tasks]

    executed = []
    blocked = []

    for t in tasks:
        if not isinstance(t, dict):
            continue
        task_id = str(t.get("task_id") or "")
        mode = str(t.get("mode") or "manual")
        claim_id = str(t.get("claim_id") or "")
        term = str(t.get("term") or "")
        task_kind = str(t.get("task_kind") or "")

        task_event(
            ledger=ledger_path,
            run_id=run_id,
            task_id=task_id,
            status="STARTED",
            mode=mode,
            claim_id=claim_id,
            term=term,
            task_kind=task_kind,
            detail=str(t.get("title") or ""),
        )

        # dispatch by mode; actual Decodo integration will be the next operator (WO-78)
        if mode in ("decodo", "online") and not caps.get("online_allowed", False):
            pkt = _offline_packet(t)
            blocked.append({"task": t, "reason": "online_not_allowed", "offline_packet": pkt})
            task_event(
                ledger=ledger_path,
                run_id=run_id,
                task_id=task_id,
                status="BLOCKED",
                mode=mode,
                claim_id=claim_id,
                term=term,
                task_kind=task_kind,
                detail="Blocked: ABX_ONLINE_ALLOWED=0",
                artifacts={"offline_packet": pkt},
            )
            continue

        if mode == "decodo" and not caps.get("decodo_available", False):
            pkt = _offline_packet(t)
            blocked.append({"task": t, "reason": "decodo_unavailable", "offline_packet": pkt})
            task_event(
                ledger=ledger_path,
                run_id=run_id,
                task_id=task_id,
                status="BLOCKED",
                mode=mode,
                claim_id=claim_id,
                term=term,
                task_kind=task_kind,
                detail="Blocked: Decodo not configured (DECODO_API_KEY missing)",
                artifacts={"offline_packet": pkt},
            )
            continue

        # Manual/offline tasks are "executed" as emitted instruction packets for the user (no hallucinated actions)
        if mode in ("manual", "offline"):
            pkt = _offline_packet(t)
            executed.append({"task": t, "result": "emitted_offline_packet", "offline_packet": pkt})
            task_event(
                ledger=ledger_path,
                run_id=run_id,
                task_id=task_id,
                status="COMPLETED",
                mode=mode,
                claim_id=claim_id,
                term=term,
                task_kind=task_kind,
                detail="Completed: offline packet emitted",
                artifacts={"offline_packet": pkt},
            )
            continue

        # Placeholder for online/decodo execution — handled in WO-78 operator
        executed.append({"task": t, "result": "deferred_to_online_operator"})
        task_event(
            ledger=ledger_path,
            run_id=run_id,
            task_id=task_id,
            status="COMPLETED",
            mode=mode,
            claim_id=claim_id,
            term=term,
            task_kind=task_kind,
            detail="Completed: deferred to online operator (WO-78)",
        )

    return {
        "version": "acquisition_execute.v0.1",
        "ts": _utc_now_iso(),
        "run_id": run_id,
        "capabilities": caps,
        "plan_path": plan_path,
        "n_tasks_considered": len(tasks),
        "executed": executed,
        "blocked": blocked,
        "notes": "Exec adapter logs task lifecycle. Online/Decodo execution is deferred to next operator.",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Execute acquisition plan with capability gating + task ledger logging")
    ap.add_argument("--plan", default="")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--ledger", default="out/ledger/task_ledger.jsonl")
    ap.add_argument("--max-tasks", type=int, default=10)
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    plan_path = args.plan or _latest("out/reports", "acquisition_plan_*.json")
    if not plan_path:
        raise SystemExit("No acquisition_plan found. Run `python -m abx.acquisition_planner` first.")

    obj = execute_plan(plan_path=plan_path, run_id=args.run_id, ledger_path=args.ledger, max_tasks=int(args.max_tasks))

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = args.out or os.path.join("out/reports", f"acquisition_execute_{stamp}.json")
    _write_json(out_path, obj)
    print(f"[ACQ_EXEC] wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
