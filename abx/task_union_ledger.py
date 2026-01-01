from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from abx.task_ledger import task_status_change


PRIORITY = {
    "VERIFY_MEDIA_ORIGIN": 100,
    "ADD_PRIMARY_ANCHORS": 90,
    "FETCH_COUNTERCLAIMS_DISJOINT": 80,
    "INCREASE_DOMAIN_DIVERSITY": 70,
    "ENTITY_GROUNDING": 60,
    "ADD_FALSIFICATION_TESTS": 50,
}

FRONT_OVERRIDES = {
    "POLLUTION": {
        "VERIFY_MEDIA_ORIGIN": 1.35,
        "ADD_PRIMARY_ANCHORS": 1.15,
    },
    "MIGRATION_SURGE": {
        "ADD_PRIMARY_ANCHORS": 1.25,
        "INCREASE_DOMAIN_DIVERSITY": 1.15,
    },
    "MIGRATION": {
        "ADD_PRIMARY_ANCHORS": 1.15,
        "INCREASE_DOMAIN_DIVERSITY": 1.1,
    },
    "AALMANAC_DECAY": {
        "INCREASE_DOMAIN_DIVERSITY": 1.1,
        "ADD_PRIMARY_ANCHORS": 1.1,
    },
    "REUPLOAD_STORM": {
        "INCREASE_DOMAIN_DIVERSITY": 1.2,
        "ADD_PRIMARY_ANCHORS": 1.15,
    },
    "SOURCE_CONVERGENCE": {
        "ADD_PRIMARY_ANCHORS": 1.2,
    },
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _utc_now_iso() -> str:
    return _utc_now().isoformat()


def _parse_iso(ts: str) -> datetime | None:
    try:
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _front_mult(front_tags: List[str], front_overrides: Dict[str, Any], task_kind: str) -> float:
    tags = [str(x).strip().upper() for x in (front_tags or []) if str(x).strip()]
    mult = 1.0
    for tag in tags:
        mult *= float(((front_overrides.get(tag) or {}).get(task_kind)) or 1.0)
    return float(mult)


def _prio(task_kind: str, front_tags: List[str]) -> float:
    base = float(PRIORITY.get(task_kind or "", 10))
    return float(base * _front_mult(front_tags, FRONT_OVERRIDES, task_kind))


def _read_jsonl(path: str) -> List[Dict[str, Any]]:
    if not path or not os.path.exists(path):
        return []
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                if isinstance(d, dict):
                    out.append(d)
            except Exception:
                continue
    return out


def _append_jsonl(path: str, obj: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _dedupe_key(t: Dict[str, Any]) -> Tuple[str, str, str]:
    cid = str(t.get("claim_id") or "")
    term = str(t.get("term") or "")
    tk = str(t.get("task_kind") or "")
    return (cid, term, tk)


def _merge_detail(a: Dict[str, Any], b: Dict[str, Any]) -> str:
    da = str(a.get("detail") or "").strip()
    db = str(b.get("detail") or "").strip()
    if not da:
        return db
    if not db:
        return da
    if db in da:
        return da
    return da + " | " + db


def _latest_task_state(events: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    state: Dict[str, Dict[str, Any]] = {}
    for e in events:
        if not isinstance(e, dict):
            continue
        kind = str(e.get("kind") or "")
        if kind == "task_event":
            tid = str(e.get("task_id") or "")
            if not tid:
                continue
            cur = state.get(tid) or {}
            cur.update(
                {
                    "task_id": tid,
                    "run_id": str(e.get("run_id") or ""),
                    "status": str(e.get("status") or ""),
                    "mode": str(e.get("mode") or ""),
                    "claim_id": str(e.get("claim_id") or ""),
                    "term": str(e.get("term") or ""),
                    "task_kind": str(e.get("task_kind") or ""),
                    "detail": str(e.get("detail") or ""),
                    "due_ts": str((e.get("artifacts") or {}).get("due_ts") or cur.get("due_ts") or ""),
                    "ts": str(e.get("ts") or ""),
                    "artifacts": e.get("artifacts") or {},
                }
            )
            state[tid] = cur
        elif kind == "task_status_changed":
            tid = str(e.get("task_id") or "")
            if not tid or tid not in state:
                continue
            state[tid]["status"] = str(
                e.get("to_status") or state[tid].get("status") or ""
            )
            state[tid]["ts"] = str(e.get("ts") or state[tid].get("ts") or "")
    return state


def _eligible(task: Dict[str, Any], now: datetime) -> bool:
    if str(task.get("status") or "") != "QUEUED":
        return False
    due = str(task.get("due_ts") or "").strip()
    if not due:
        return True
    dt = _parse_iso(due)
    if not dt:
        return True
    return dt <= now


def main() -> int:
    ap = argparse.ArgumentParser(
        description="WO-93: build acquisition batch by unioning eligible QUEUED tasks from task ledger"
    )
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--task-ledger", default="out/ledger/task_ledger.jsonl")
    ap.add_argument("--union-ledger", default="out/ledger/union_ledger.jsonl")
    ap.add_argument("--out", default="")
    ap.add_argument("--max", type=int, default=60)
    ap.add_argument("--dry-run", action="store_true", default=False)
    args = ap.parse_args()

    events = _read_jsonl(args.task_ledger)
    state = _latest_task_state(events)
    now = _utc_now()

    eligible = [t for t in state.values() if _eligible(t, now)]

    chosen: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
    dropped = 0
    for t in eligible:
        key = _dedupe_key(t)
        if key not in chosen:
            chosen[key] = dict(t)
            continue
        cur = chosen[key]
        t_tags = ((t.get("artifacts") or {}).get("front_tags") or [])
        c_tags = ((cur.get("artifacts") or {}).get("front_tags") or [])
        if _prio(str(t.get("task_kind") or ""), t_tags) > _prio(
            str(cur.get("task_kind") or ""), c_tags
        ):
            lost = cur
            cur = dict(t)
            cur["detail"] = _merge_detail(t, lost)
            chosen[key] = cur
        else:
            cur["detail"] = _merge_detail(cur, t)
            chosen[key] = cur

        dropped += 1
        _append_jsonl(
            args.union_ledger,
            {
                "kind": "task_dedup_dropped",
                "ts": _utc_now_iso(),
                "run_id": args.run_id,
                "dedupe_key": {
                    "claim_id": key[0],
                    "term": key[1],
                    "task_kind": key[2],
                },
                "dropped_task_id": str(t.get("task_id") or ""),
                "kept_task_id": str(chosen[key].get("task_id") or ""),
                "notes": "Duplicate task dropped during ledger union; details merged into kept task.",
            },
        )

    tasks = list(chosen.values())

    def _sort_key(x: Dict[str, Any]) -> tuple:
        cid = str(x.get("claim_id") or "")
        term = str(x.get("term") or "")
        ft = ((x.get("artifacts") or {}).get("front_tags") or [])
        return (-_prio(str(x.get("task_kind") or ""), ft), 0 if cid else 1, term)

    tasks = sorted(tasks, key=_sort_key)[: int(args.max)]

    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    batch_id = f"acq_batch_{stamp}"

    out_obj = {
        "version": "task_union_ledger.v0.1",
        "ts": _utc_now_iso(),
        "run_id": args.run_id,
        "batch_id": batch_id,
        "stats": {
            "n_tasks_state": len(state),
            "n_eligible": len(eligible),
            "n_dedup_dropped": int(dropped),
            "n_out": len(tasks),
            "dry_run": bool(args.dry_run),
        },
        "tasks": [
            {
                "task_id": t.get("task_id"),
                "run_id": t.get("run_id"),
                "claim_id": t.get("claim_id"),
                "term": t.get("term"),
                "task_kind": t.get("task_kind"),
                "mode": t.get("mode"),
                "detail": t.get("detail"),
            }
            for t in tasks
        ],
        "notes": "Single acquisition batch derived from append-only task ledger (eligible QUEUED tasks).",
    }

    out_path = args.out or os.path.join("out/reports", f"{batch_id}.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_obj, f, ensure_ascii=False, indent=2)

    _append_jsonl(
        args.union_ledger,
        {
            "kind": "task_batch_selected",
            "ts": _utc_now_iso(),
            "run_id": args.run_id,
            "batch_id": batch_id,
            "n_out": len(tasks),
            "dry_run": bool(args.dry_run),
            "out_path": out_path,
            "notes": "WO-93 selected tasks into acquisition batch from task ledger.",
        },
    )

    if not args.dry_run:
        for t in tasks:
            tid = str(t.get("task_id") or "")
            if not tid:
                continue
            task_status_change(
                ledger=args.task_ledger,
                run_id=args.run_id,
                task_id=tid,
                from_status="QUEUED",
                to_status="IN_PROGRESS",
                reason="BATCHED_FOR_ACQUISITION",
                batch_id=batch_id,
                artifacts={"acq_batch": out_path},
            )

    print(
        f"[UNION_LEDGER] wrote: {out_path} out={len(tasks)} eligible={len(eligible)} dropped={dropped} dry={args.dry_run}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
