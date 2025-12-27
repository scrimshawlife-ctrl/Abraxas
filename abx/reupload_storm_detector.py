from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List

from abx.task_ledger import task_event


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _utc_now_iso() -> str:
    return _utc_now().isoformat()


def _stamp() -> str:
    return _utc_now().strftime("%Y%m%dT%H%M%SZ")


def _read_jsonl(path: str) -> List[Dict[str, Any]]:
    if not path or not os.path.exists(path):
        return []
    out: List[Dict[str, Any]] = []
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


def _write_json(path: str, obj: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def _host(url: str) -> str:
    m = re.match(r"^https?://([^/]+)", (url or "").strip())
    return (m.group(1).lower() if m else "")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="WO-100: detect reupload storms from media fingerprint index and emit fronts/tasks"
    )
    ap.add_argument("--run-id", required=True)
    ap.add_argument(
        "--fp-index-ledger", default="out/ledger/media_fingerprint_index.jsonl"
    )
    ap.add_argument("--origin-ledger", default="out/ledger/media_origin_ledger.jsonl")
    ap.add_argument("--fronts-ledger", default="out/ledger/reupload_fronts.jsonl")
    ap.add_argument("--task-ledger", default="out/ledger/task_ledger.jsonl")
    ap.add_argument("--out", default="")
    ap.add_argument("--window", type=int, default=400)
    ap.add_argument("--storm-domains", type=int, default=3)
    args = ap.parse_args()

    fp_events = [
        e
        for e in _read_jsonl(args.fp_index_ledger)
        if e.get("kind") == "media_fingerprint_seen"
    ]
    tail = fp_events[-int(args.window) :]

    origin = [
        e
        for e in _read_jsonl(args.origin_ledger)
        if e.get("kind") == "media_origin" and bool(e.get("ok"))
    ]
    final_by_task: Dict[str, str] = {}
    anchor_by_task: Dict[str, str] = {}
    for o in origin[-2000:]:
        tid = str(o.get("task_id") or "")
        if not tid:
            continue
        final_by_task[tid] = _host(str(o.get("final_url") or o.get("url") or ""))
        anchor_by_task[tid] = str(o.get("anchor_id") or "")

    occ: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for e in tail:
        fp = str(e.get("fingerprint") or "")
        if not fp:
            continue
        occ[fp].append(e)

    storms = []
    emitted_tasks = 0
    for fp, rows in occ.items():
        domains = sorted({str(r.get("domain") or "") for r in rows if r.get("domain")})
        if len(domains) < int(args.storm_domains):
            continue

        finals = []
        anchors = []
        for r in rows:
            tid = str(r.get("task_id") or "")
            if tid in final_by_task and final_by_task[tid]:
                finals.append(final_by_task[tid])
            if tid in anchor_by_task and anchor_by_task[tid]:
                anchors.append(anchor_by_task[tid])
        final_counts = Counter(finals)
        top_final, top_n = (
            final_counts.most_common(1)[0] if final_counts else ("", 0)
        )
        convergence = bool(top_final and top_n >= 2)

        front_tags = ["REUPLOAD_STORM", "POLLUTION"]
        if convergence:
            front_tags.append("SOURCE_CONVERGENCE")

        strength = min(1.0, len(domains) / 8.0)
        anchor_id = anchors[0] if anchors else ""

        front_ev = {
            "kind": "reupload_front",
            "ts": _utc_now_iso(),
            "run_id": args.run_id,
            "fingerprint": fp,
            "domains": domains,
            "domain_count": len(domains),
            "converged_final_host": top_final,
            "convergence_votes": int(top_n),
            "front_tags": front_tags,
            "strength": float(strength),
            "anchor_id": anchor_id,
            "notes": "WO-100: fingerprint seen across multiple domains; potential coordinated propagation / reupload storm.",
        }
        _append_jsonl(args.fronts_ledger, front_ev)
        storms.append(front_ev)

        task_kinds = [
            "ADD_PRIMARY_ANCHORS",
            "INCREASE_DOMAIN_DIVERSITY",
            "FETCH_COUNTERCLAIMS_DISJOINT",
        ]
        for tk in task_kinds:
            tid = f"storm_{tk.lower()}_{abs(hash((fp, tk, args.run_id))) % (10**10)}"
            detail = (
                f"WO-100 REUPLOAD_STORM fp={fp[:12]} domains={len(domains)} "
                f"converged={convergence} top_final={top_final} | "
                f"domains={','.join(domains[:8])}"
            )
            task_event(
                ledger=args.task_ledger,
                run_id=args.run_id,
                task_id=tid,
                status="QUEUED",
                mode="REUPLOAD_STORM",
                claim_id="",
                term="",
                task_kind=tk,
                detail=detail,
                artifacts={
                    "front_tags": front_tags,
                    "fingerprint": fp,
                    "domains": domains,
                    "anchor_id": anchor_id,
                    "converged_final_host": top_final,
                },
            )
            emitted_tasks += 1

    out_path = args.out or os.path.join(
        "out/reports", f"reupload_storms_{_stamp()}.json"
    )
    _write_json(
        out_path,
        {
            "version": "reupload_storms.v0.1",
            "ts": _utc_now_iso(),
            "run_id": args.run_id,
            "window": int(args.window),
            "storm_domains": int(args.storm_domains),
            "n_storms": len(storms),
            "storms": storms,
            "tasks_emitted": emitted_tasks,
            "notes": "Materialized report; stream in reupload_fronts.jsonl",
        },
    )
    print(
        f"[STORMS] wrote: {out_path} storms={len(storms)} tasks={emitted_tasks}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
