from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

from abx.task_ledger import task_status_change


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _append_jsonl(path: str, obj: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _read_json(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _count_lines(path: str) -> int:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return sum(1 for line in f if line.strip())
    except Exception:
        return 0


def _roi(task_kind: str, outcome: Dict[str, Any]) -> float:
    tk = str(task_kind or "")
    a = int(outcome.get("anchors_added") or 0)
    d = int(outcome.get("domains_added") or 0)
    c = int(outcome.get("counterclaims_added") or 0)
    mv = bool(outcome.get("media_verified") or False)
    if tk == "ADD_PRIMARY_ANCHORS":
        return float(min(1.0, a / 3.0))
    if tk == "INCREASE_DOMAIN_DIVERSITY":
        return float(min(1.0, d / 4.0))
    if tk == "FETCH_COUNTERCLAIMS_DISJOINT":
        return float(min(1.0, c / 3.0))
    if tk == "VERIFY_MEDIA_ORIGIN":
        return 1.0 if mv else 0.0
    return float(min(1.0, (a + d + c) / 6.0))


def _execute_one_task(task: Dict[str, Any], provider: str) -> Dict[str, Any]:
    """
    Placeholder executor: returns a structured outcome without network side effects.
    Replace with real acquisition driver in your environment.
    """
    return {
        "status": "FAILED",
        "anchors_added": 0,
        "domains_added": 0,
        "counterclaims_added": 0,
        "media_verified": False,
        "error": "executor_not_implemented",
        "provider": provider,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Execute acquisition tasks from a batch")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--in", dest="in_path", required=True)
    ap.add_argument("--provider", default="")
    ap.add_argument("--task-ledger", default="out/ledger/task_ledger.jsonl")
    ap.add_argument("--anchor-ledger", default="out/ledger/anchor_ledger.jsonl")
    ap.add_argument("--outcomes-ledger", default="out/ledger/task_outcomes.jsonl")
    ap.add_argument(
        "--media-origin-report",
        default="",
        help="Optional media_origin_verify_*.json to mark media_verified outcomes",
    )
    args = ap.parse_args()

    batch = _read_json(args.in_path)
    tasks = batch.get("tasks") if isinstance(batch.get("tasks"), list) else []
    media_ok_by_task: Dict[str, bool] = {}
    if args.media_origin_report:
        try:
            rep = _read_json(args.media_origin_report)
            for it in rep.get("items") if isinstance(rep.get("items"), list) else []:
                if not isinstance(it, dict):
                    continue
                tid = str(it.get("task_id") or "")
                if tid:
                    media_ok_by_task[tid] = bool(it.get("ok"))
        except Exception:
            media_ok_by_task = {}

    for t in tasks:
        if not isinstance(t, dict):
            continue
        task_id = str(t.get("task_id") or "")
        claim_id = str(t.get("claim_id") or "")
        term = str(t.get("term") or "")
        task_kind = str(t.get("task_kind") or "")
        detail = str(t.get("detail") or "")

        before_anchors = _count_lines(args.anchor_ledger)

        status = "FAILED"
        outcome: Dict[str, Any] = {
            "anchors_added": 0,
            "domains_added": 0,
            "counterclaims_added": 0,
            "media_verified": False,
        }

        if not args.provider:
            status = "NEEDS_OFFLINE"
            outcome["offline_required_reason"] = "no_provider_configured"
        else:
            try:
                result = _execute_one_task(t, provider=args.provider)
                if isinstance(result, dict):
                    outcome.update(result)
                    status = str(result.get("status") or status)
                else:
                    status = "FAILED"
            except Exception as e:
                status = "FAILED"
                outcome["error"] = repr(e)

        after_anchors = _count_lines(args.anchor_ledger)
        anchors_added = max(0, after_anchors - before_anchors)
        outcome["anchors_added"] = int(outcome.get("anchors_added") or anchors_added)
        if task_id and task_kind == "VERIFY_MEDIA_ORIGIN":
            if bool(media_ok_by_task.get(task_id, False)):
                outcome["media_verified"] = True

        roi = _roi(task_kind, outcome)

        _append_jsonl(
            args.outcomes_ledger,
            {
                "kind": "task_outcome",
                "ts": _utc_now_iso(),
                "run_id": args.run_id,
                "task_id": task_id,
                "claim_id": claim_id,
                "term": term,
                "task_kind": task_kind,
                "status": status,
                "detail": detail,
                "outcome": outcome,
                "roi": float(roi),
                "batch_in": args.in_path,
                "provider": args.provider,
                "notes": "WO-94: acquisition outcome event; deterministic ROI heuristic.",
            },
        )

        task_status_change(
            ledger=args.task_ledger,
            run_id=args.run_id,
            task_id=task_id,
            from_status="IN_PROGRESS",
            to_status=status,
            reason="ACQUISITION_EXECUTED",
            batch_id=str(batch.get("batch_id") or ""),
            artifacts={"outcome_ledger": args.outcomes_ledger, "roi": roi},
        )

    print(f"[ACQ] processed tasks={len(tasks)} outcomes={args.outcomes_ledger}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
