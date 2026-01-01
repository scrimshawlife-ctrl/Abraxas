from __future__ import annotations

import argparse
import glob
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple


PRIORITY = {
    "VERIFY_MEDIA_ORIGIN": 100,
    "ADD_PRIMARY_ANCHORS": 90,
    "FETCH_COUNTERCLAIMS_DISJOINT": 80,
    "INCREASE_DOMAIN_DIVERSITY": 70,
    "ENTITY_GROUNDING": 60,
    "ADD_FALSIFICATION_TESTS": 50,
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _append_jsonl(path: str, obj: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _prio(task_kind: str) -> int:
    return int(PRIORITY.get(task_kind or "", 10))


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


def main() -> int:
    ap = argparse.ArgumentParser(
        description="WO-90: union outboxes (review + weather) into one acquisition batch"
    )
    ap.add_argument("--run-id", required=True)
    ap.add_argument(
        "--review",
        default="",
        help="Path to review_tasks.json (default: out/reports/review_tasks.json)",
    )
    ap.add_argument(
        "--weather",
        default="",
        help="Path to weather_tasks_bound_*.json (default: latest)",
    )
    ap.add_argument("--out", default="")
    ap.add_argument("--union-ledger", default="out/ledger/union_ledger.jsonl")
    ap.add_argument("--max", type=int, default=60)
    args = ap.parse_args()

    if not args.review:
        args.review = "out/reports/review_tasks.json"
    if not args.weather:
        wp = sorted(glob.glob("out/reports/weather_tasks_bound_*.json"))
        args.weather = wp[-1] if wp else ""

    rev = _read_json(args.review) if args.review and os.path.exists(args.review) else {}
    wea = _read_json(args.weather) if args.weather and os.path.exists(args.weather) else {}

    rev_tasks = rev.get("tasks") if isinstance(rev.get("tasks"), list) else []
    wea_tasks = wea.get("tasks") if isinstance(wea.get("tasks"), list) else []

    chosen: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
    dropped = 0
    for src, arr in [("review", rev_tasks), ("weather", wea_tasks)]:
        for t in arr:
            if not isinstance(t, dict):
                continue
            key = _dedupe_key(t)
            if key not in chosen:
                tt = dict(t)
                tt["source_stream"] = src
                chosen[key] = tt
                continue
            cur = chosen[key]
            if _prio(str(t.get("task_kind") or "")) > _prio(
                str(cur.get("task_kind") or "")
            ):
                kept, lost = t, cur
                cur = dict(kept)
                cur["source_stream"] = src
                cur["detail"] = _merge_detail(kept, lost)
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
                    "dropped_from": src,
                    "kept_task": {
                        "task_id": cur.get("task_id"),
                        "claim_id": cur.get("claim_id"),
                        "term": cur.get("term"),
                        "task_kind": cur.get("task_kind"),
                        "source_stream": cur.get("source_stream"),
                    },
                    "dropped_task": {
                        "task_id": t.get("task_id"),
                        "claim_id": t.get("claim_id"),
                        "term": t.get("term"),
                        "task_kind": t.get("task_kind"),
                    },
                    "notes": "Duplicate task dropped during union; details merged into kept task.",
                },
            )

    tasks = list(chosen.values())

    def _sort_key(x: Dict[str, Any]) -> tuple:
        cid = str(x.get("claim_id") or "")
        term = str(x.get("term") or "")
        return (-_prio(str(x.get("task_kind") or "")), 0 if cid else 1, term)

    tasks = sorted(tasks, key=_sort_key)[: int(args.max)]

    obj = {
        "version": "task_union.v0.1",
        "ts": _utc_now_iso(),
        "run_id": args.run_id,
        "inputs": {"review": args.review, "weather": args.weather},
        "stats": {
            "n_review": len(rev_tasks),
            "n_weather": len(wea_tasks),
            "n_dedup_dropped": int(dropped),
            "n_out": len(tasks),
        },
        "tasks": tasks,
        "notes": "Union of review + weather streams into a single acquisition batch. Priority-sorted. Dedup logged.",
    }

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = args.out or os.path.join("out/reports", f"acq_batch_{stamp}.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    print(f"[UNION] wrote: {out_path} out={len(tasks)} dropped={dropped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
