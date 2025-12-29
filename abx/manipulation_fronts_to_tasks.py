from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, List

from abx.task_ledger import task_event


def _utc_now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


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


def main() -> int:
    ap = argparse.ArgumentParser(
        description="WO-97: convert manipulation fronts into tagged acquisition tasks"
    )
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--metrics-ledger", default="out/ledger/manipulation_metrics.jsonl")
    ap.add_argument("--task-ledger", default="out/ledger/task_ledger.jsonl")
    ap.add_argument("--max-events", type=int, default=200)
    args = ap.parse_args()

    evs = _read_jsonl(args.metrics_ledger)
    tail = [
        e for e in evs if e.get("kind") == "manipulation_metrics"
    ][-int(args.max_events) :]

    n_tasks = 0
    for e in tail:
        fronts = e.get("fronts") if isinstance(e.get("fronts"), list) else []
        if not fronts:
            continue
        aid = str(e.get("anchor_id") or "")
        dom = str(e.get("domain") or "")
        scores = e.get("scores") if isinstance(e.get("scores"), dict) else {}
        mii = float(scores.get("MII") or 0.0)
        pps = float(scores.get("PPS") or 0.0)
        cas = float(scores.get("CAS") or 0.0)

        for f in fronts:
            fk = str(f.get("front_kind") or "").upper()
            strength = float(f.get("strength") or 0.0)
            reason = str(f.get("reason") or "")

            task_kinds = []
            if fk in ("DEEPFAKE_SUSPECT", "POLLUTION"):
                task_kinds.append("VERIFY_MEDIA_ORIGIN")
                task_kinds.append("ADD_PRIMARY_ANCHORS")
            if fk == "PSYOP_PATTERN":
                task_kinds.append("INCREASE_DOMAIN_DIVERSITY")
                task_kinds.append("FETCH_COUNTERCLAIMS_DISJOINT")

            for tk in task_kinds:
                tid = (
                    f"manip_{fk.lower()}_{tk.lower()}_"
                    f"{abs(hash((aid, fk, tk, args.run_id))) % (10**10)}"
                )
                detail = (
                    f"WO-97 {fk} strength={strength:.2f} reason={reason} | "
                    f"scores(PPS={pps:.2f},MII={mii:.2f},CAS={cas:.2f}) | "
                    f"anchor_id={aid} domain={dom}"
                )
                task_event(
                    ledger=args.task_ledger,
                    run_id=args.run_id,
                    task_id=tid,
                    status="QUEUED",
                    mode="MANIPULATION_METRICS",
                    claim_id="",
                    term="",
                    task_kind=tk,
                    detail=detail,
                    artifacts={
                        "front_tags": [fk],
                        "anchor_id": aid,
                        "domain": dom,
                        "scores": scores,
                        "front": f,
                        "needs_url": True if tk == "VERIFY_MEDIA_ORIGIN" else False,
                    },
                )
                n_tasks += 1

    print(f"[MANIP_TASKS] queued={n_tasks}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
