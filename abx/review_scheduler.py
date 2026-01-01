from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from abx.horizon import next_review
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


def _parse_ts(ts: str) -> Optional[datetime]:
    try:
        if not ts:
            return None
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _mk_task(
    *,
    run_id: str,
    task_id: str,
    claim_id: str,
    term: str,
    task_kind: str,
    mode: str,
    detail: str,
    expected_uplift: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "task_id": task_id,
        "run_id": run_id,
        "claim_id": claim_id,
        "term": term,
        "task_kind": task_kind,
        "mode": mode,
        "detail": detail,
        "expected_uplift": expected_uplift or {},
    }


def _choose_tasks(
    *,
    tpv_entry: Dict[str, Any],
    claim_deficits: Dict[str, Any],
) -> List[str]:
    """
    Deterministic policy:
    - High TPV => verification + counterclaims + primary anchors
    - Low TPV + unstable => falsification + domain diversity + grounding
    """
    tpv = float(tpv_entry.get("TPV") or 0.0)
    unstable = bool(claim_deficits.get("unstable"))
    low_pis = bool(claim_deficits.get("low_pis"))
    weak_primary = bool(claim_deficits.get("weak_primary"))
    weak_domains = bool(claim_deficits.get("weak_domains"))
    polluted = bool(claim_deficits.get("polluted"))

    tasks: List[str] = []
    if tpv >= 0.55 or polluted:
        tasks.extend(
            [
                "VERIFY_MEDIA_ORIGIN",
                "ADD_PRIMARY_ANCHORS",
                "FETCH_COUNTERCLAIMS_DISJOINT",
            ]
        )
        if unstable:
            tasks.append("ADD_FALSIFICATION_TESTS")
    else:
        if unstable or low_pis:
            tasks.append("ADD_FALSIFICATION_TESTS")
        if weak_domains:
            tasks.append("INCREASE_DOMAIN_DIVERSITY")
        if weak_primary:
            tasks.append("ADD_PRIMARY_ANCHORS")
        tasks.append("ENTITY_GROUNDING")

    out = []
    for t in tasks:
        if t not in out:
            out.append(t)
    return out


def _load_latest_report(pattern: str) -> str:
    import glob

    paths = sorted(glob.glob(pattern))
    return paths[-1] if paths else ""


def _load_deficits(path: str) -> Dict[str, Any]:
    obj = _read_json(path)
    claims = obj.get("claims") if isinstance(obj.get("claims"), dict) else {}
    out = defaultdict(dict)
    for cid, entry in claims.items():
        if isinstance(entry, dict):
            out[str(cid)] = entry
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="WO-84: τ review scheduler for forecasts")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--forecast-ledger", default="out/ledger/forecast_ledger.jsonl")
    ap.add_argument(
        "--outbox", default="out/reports/review_tasks.json"
    )  # tasks to feed to acquisition_execute
    ap.add_argument("--scheduler-ledger", default="out/ledger/scheduler_ledger.jsonl")
    ap.add_argument("--task-ledger", default="out/ledger/task_ledger.jsonl")
    ap.add_argument("--truth-pollution", default="")
    ap.add_argument("--deficits", default="")
    ap.add_argument("--max-due", type=int, default=10)
    args = ap.parse_args()

    if not args.truth_pollution:
        args.truth_pollution = _load_latest_report("out/reports/truth_pollution_*.json")
    tpv = _read_json(args.truth_pollution) if args.truth_pollution else {}
    tpv_claims = tpv.get("claims") if isinstance(tpv.get("claims"), dict) else {}

    if not args.deficits:
        args.deficits = _load_latest_report("out/reports/deficits_*.json")
    def_claims = _load_deficits(args.deficits) if args.deficits else {}

    forecasts = [
        f for f in _read_jsonl(args.forecast_ledger) if f.get("kind") == "forecast"
    ]
    now = _utc_now()

    due = []
    for f in forecasts:
        nxt = _parse_ts(str(f.get("next_review_ts") or ""))
        if nxt and nxt <= now:
            due.append(f)

    due = due[: int(args.max_due)]
    emitted_tasks: List[Dict[str, Any]] = []

    for f in due:
        fid = str(f.get("forecast_id") or "")
        title = str(f.get("title") or "")
        claim_id = str((f.get("provenance") or {}).get("claim_id") or "")
        term = str((f.get("provenance") or {}).get("term") or "")
        horizon = (f.get("horizon") or {}).get("key") or ""

        _append_jsonl(
            args.scheduler_ledger,
            {
                "kind": "forecast_due_detected",
                "ts": _utc_now_iso(),
                "run_id": args.run_id,
                "forecast_id": fid,
                "claim_id": claim_id,
                "horizon": horizon,
                "title": title,
            },
        )

        tpv_entry = tpv_claims.get(claim_id, {}) if claim_id else {}
        def_entry = def_claims.get(claim_id, {}) if claim_id else {}
        kinds = _choose_tasks(tpv_entry=tpv_entry, claim_deficits=def_entry)

        for i, tk in enumerate(kinds):
            task_id = f"rev_{fid}_{i}_{int(now.timestamp())}"
            detail = (
                f"WO-84 review: forecast={fid} horizon={horizon} TPV={tpv_entry.get('TPV','?')}"
            )
            emitted_tasks.append(
                _mk_task(
                    run_id=args.run_id,
                    task_id=task_id,
                    claim_id=claim_id,
                    term=term,
                    task_kind=tk,
                    mode="AUTO_REVIEW",
                    detail=detail,
                )
            )

            task_event(
                ledger=args.task_ledger,
                run_id=args.run_id,
                task_id=task_id,
                status="QUEUED",
                mode="AUTO_REVIEW",
                claim_id=claim_id,
                term=term,
                task_kind=tk,
                detail=detail,
                artifacts={"forecast_id": fid, "horizon": horizon, "tpv": tpv_entry},
            )

        ts = _utc_now_iso()
        base_next = next_review(ts, str(horizon or "H1W"))
        tau_days = int((tpv_entry.get("modulators") or {}).get("tau_review_days") or 0)
        if tau_days > 0:
            dt = _parse_ts(ts)
            base_next = (
                (dt + timedelta(days=int(tau_days))).replace(microsecond=0).isoformat()
                if dt
                else base_next
            )

        _append_jsonl(
            args.scheduler_ledger,
            {
                "kind": "forecast_review_scheduled",
                "ts": ts,
                "run_id": args.run_id,
                "forecast_id": fid,
                "next_review_ts": base_next,
                "policy": {"horizon": horizon, "tau_review_days": tau_days},
            },
        )

    out_obj = {
        "version": "review_scheduler.v0.1",
        "ts": _utc_now_iso(),
        "run_id": args.run_id,
        "n_due": len(due),
        "n_tasks": len(emitted_tasks),
        "tasks": emitted_tasks,
        "notes": "WO-84 schedules review-driven acquisition tasks from due forecasts. Feed tasks into acquisition_execute.",
    }
    os.makedirs(os.path.dirname(args.outbox), exist_ok=True)
    with open(args.outbox, "w", encoding="utf-8") as f:
        json.dump(out_obj, f, ensure_ascii=False, indent=2)
    print(f"[REVIEW_SCHED] wrote outbox: {args.outbox} tasks={len(emitted_tasks)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
