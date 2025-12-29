from __future__ import annotations

import argparse
import glob
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

from abx.task_ledger import task_event


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _utc_now_iso() -> str:
    return _utc_now().isoformat()


def _read_json(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def main() -> int:
    ap = argparse.ArgumentParser(
        description="WO-88: convert mimetic weather fronts into acquisition tasks"
    )
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--task-ledger", default="out/ledger/task_ledger.jsonl")
    ap.add_argument("--weather", default="")
    ap.add_argument("--outbox", default="")
    ap.add_argument("--max-terms", type=int, default=10)
    args = ap.parse_args()

    if not args.weather:
        wp = sorted(glob.glob("out/reports/mimetic_weather_*.json"))
        args.weather = wp[-1] if wp else ""
    if not args.weather:
        raise SystemExit("No mimetic_weather report found.")

    weather = _read_json(args.weather)
    fronts = weather.get("fronts") if isinstance(weather.get("fronts"), list) else []

    tasks: List[Dict[str, Any]] = []
    now = _utc_now()

    def add_task(term: str, task_kind: str, detail: str, front_tag: str) -> None:
        tid = (
            f"wx_{task_kind.lower()}_"
            f"{abs(hash((term, task_kind, int(now.timestamp())))) % (10**10)}"
        )
        tasks.append(
            {
                "task_id": tid,
                "run_id": args.run_id,
                "claim_id": "",
                "term": term,
                "task_kind": task_kind,
                "mode": "WEATHER",
                "detail": detail,
            }
        )
        task_event(
            ledger=args.task_ledger,
            run_id=args.run_id,
            task_id=tid,
            status="QUEUED",
            mode="WEATHER",
            claim_id="",
            term=term,
            task_kind=task_kind,
            detail=detail,
            artifacts={"weather_report": args.weather, "front_tags": [front_tag]},
        )

    def pick_terms(f: Dict[str, Any]) -> List[str]:
        ts = f.get("terms")
        if isinstance(ts, list):
            out = []
            for t in ts:
                t = str(t or "").strip()
                if t and t not in out:
                    out.append(t)
            return out[: int(args.max_terms)]
        return []

    for f in fronts:
        if not isinstance(f, dict):
            continue
        front = str(f.get("front") or "")
        terms = pick_terms(f)
        if not terms:
            continue
        front_tag = front.strip().upper() if front.strip() else "UNKNOWN"

        if front == "NEWBORN":
            for t in terms:
                add_task(
                    t,
                    "INCREASE_DOMAIN_DIVERSITY",
                    f"WO-88 NEWBORN front: expand domains for term={t}",
                    front_tag,
                )
                add_task(
                    t,
                    "ENTITY_GROUNDING",
                    f"WO-88 NEWBORN front: ground entities for term={t}",
                    front_tag,
                )
        elif front == "MIGRATION":
            for t in terms:
                add_task(
                    t,
                    "ADD_PRIMARY_ANCHORS",
                    f"WO-88 MIGRATION front: seek primary anchors for term={t}",
                    front_tag,
                )
                add_task(
                    t,
                    "FETCH_COUNTERCLAIMS_DISJOINT",
                    f"WO-88 MIGRATION front: fetch counterclaims for term={t}",
                    front_tag,
                )
        elif front == "POLLUTION":
            for t in terms:
                add_task(
                    t,
                    "VERIFY_MEDIA_ORIGIN",
                    f"WO-88 POLLUTION front: verify origin for term={t}",
                    front_tag,
                )
                add_task(
                    t,
                    "ADD_PRIMARY_ANCHORS",
                    f"WO-88 POLLUTION front: increase primary anchors for term={t}",
                    front_tag,
                )
        elif front == "AMPLIFY":
            for t in terms:
                add_task(
                    t,
                    "INCREASE_DOMAIN_DIVERSITY",
                    f"WO-88 AMPLIFY front: diversify anchors for term={t}",
                    front_tag,
                )
        elif front == "DRIFT":
            for t in terms:
                add_task(
                    t,
                    "ADD_FALSIFICATION_TESTS",
                    f"WO-88 DRIFT front: add falsification tests for term={t}",
                    front_tag,
                )

    out_obj = {
        "version": "weather_to_tasks.v0.1",
        "ts": _utc_now_iso(),
        "run_id": args.run_id,
        "weather": args.weather,
        "n_tasks": len(tasks),
        "tasks": tasks,
        "notes": "Term-driven tasks derived from mimetic weather fronts. Downstream can bind term->claim clusters.",
    }

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = args.outbox or os.path.join(
        "out/reports", f"weather_tasks_{stamp}.json"
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_obj, f, ensure_ascii=False, indent=2)
    print(f"[WX_TASKS] wrote: {out_path} tasks={len(tasks)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
