from __future__ import annotations

import argparse
import glob
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Set, Tuple


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


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


def _latest(path_glob: str) -> str:
    paths = sorted(glob.glob(path_glob))
    return paths[-1] if paths else ""


def main() -> int:
    ap = argparse.ArgumentParser(description="WO-81: compile attribution graph (task -> anchors -> edges -> claims)")
    ap.add_argument("--task-ledger", default="out/ledger/task_ledger.jsonl")
    ap.add_argument("--anchor-ledger", default="out/ledger/anchor_ledger.jsonl")
    ap.add_argument("--evidence-ledger", default="out/ledger/evidence_graph.jsonl")
    ap.add_argument("--resolver-report", default="")  # optional online_resolver_*.json
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    resolver_path = args.resolver_report or _latest("out/reports/online_resolver_*.json")
    resolver = _read_json(resolver_path) if resolver_path else {}
    task_anchor_map = resolver.get("task_anchor_map") if isinstance(resolver.get("task_anchor_map"), dict) else {}

    # Build anchor->(task_id, claim_id) from anchor ledger
    anchors = _read_jsonl(args.anchor_ledger)
    anchor_to_task: Dict[str, str] = {}
    anchor_to_claim: Dict[str, str] = {}
    task_to_anchors: Dict[str, Set[str]] = {}
    claim_to_anchors: Dict[str, Set[str]] = {}

    for a in anchors:
        if not isinstance(a, dict):
            continue
        aid = str(a.get("anchor_id") or "")
        tid = str(a.get("task_id") or "")
        cid = str(a.get("claim_id") or "")
        if not aid:
            continue
        if tid:
            anchor_to_task[aid] = tid
            task_to_anchors.setdefault(tid, set()).add(aid)
        if cid:
            anchor_to_claim[aid] = cid
            claim_to_anchors.setdefault(cid, set()).add(aid)

    # Merge in resolver task_anchor_map (sometimes anchor ledger might be delayed)
    for tid, ids in task_anchor_map.items():
        if not isinstance(ids, list):
            continue
        for aid in ids:
            aid = str(aid or "")
            if not aid:
                continue
            task_to_anchors.setdefault(str(tid), set()).add(aid)
            if aid not in anchor_to_task:
                anchor_to_task[aid] = str(tid)

    # Parse evidence ledger for anchor_claim_link edges
    edges = _read_jsonl(args.evidence_ledger)
    task_to_edges: Dict[str, List[Dict[str, Any]]] = {}
    claim_to_tasks: Dict[str, Set[str]] = {}

    for e in edges:
        if not isinstance(e, dict):
            continue
        if str(e.get("kind") or "") != "anchor_claim_link":
            continue
        aid = str(e.get("anchor_id") or "")
        cid = str(e.get("claim_id") or "")
        rel = str(e.get("relation") or "")
        if not aid or not cid:
            continue
        tid = anchor_to_task.get(aid, "")
        if tid:
            task_to_edges.setdefault(tid, []).append({
                "anchor_id": aid,
                "claim_id": cid,
                "relation": rel,
                "url": e.get("url"),
                "domain": e.get("domain"),
                "ts": e.get("ts"),
            })
            claim_to_tasks.setdefault(cid, set()).add(tid)

    # Task meta from task ledger (latest completed status)
    task_events = _read_jsonl(args.task_ledger)
    task_meta: Dict[str, Dict[str, Any]] = {}
    for te in task_events:
        if not isinstance(te, dict):
            continue
        if te.get("kind") != "task_event":
            continue
        tid = str(te.get("task_id") or "")
        if not tid:
            continue
        # last-write-wins
        task_meta[tid] = {
            "task_kind": te.get("task_kind"),
            "mode": te.get("mode"),
            "status": te.get("status"),
            "claim_id": te.get("claim_id"),
            "term": te.get("term"),
            "detail": te.get("detail"),
            "ts": te.get("ts"),
            "run_id": te.get("run_id"),
        }

    tasks_out = []
    for tid, aset in task_to_anchors.items():
        edges_list = task_to_edges.get(tid, [])
        claims_touched = sorted(list({str(x.get("claim_id") or "") for x in edges_list if isinstance(x, dict)} - {""}))
        tasks_out.append({
            "task_id": tid,
            "meta": task_meta.get(tid, {}),
            "n_anchors": len(aset),
            "anchors": sorted(list(aset)),
            "n_edges": len(edges_list),
            "edges": edges_list,
            "claims_touched": claims_touched,
        })

    claims_out = []
    for cid, tset in claim_to_tasks.items():
        claims_out.append({
            "claim_id": cid,
            "tasks": sorted(list(tset)),
            "n_tasks": len(tset),
            "n_anchors": len(claim_to_anchors.get(cid, set())),
        })

    out_obj = {
        "version": "attribution_graph.v0.1",
        "ts": _utc_now_iso(),
        "inputs": {
            "task_ledger": args.task_ledger,
            "anchor_ledger": args.anchor_ledger,
            "evidence_ledger": args.evidence_ledger,
            "resolver_report": resolver_path,
        },
        "tasks": sorted(tasks_out, key=lambda x: (x.get("n_edges", 0), x.get("n_anchors", 0)), reverse=True),
        "claims": sorted(claims_out, key=lambda x: x.get("n_tasks", 0), reverse=True),
        "notes": "Compiled attribution graph linking tasks to anchors and edges to the claims they touched.",
    }

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = args.out or os.path.join("out/reports", f"attribution_graph_{stamp}.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_obj, f, ensure_ascii=False, indent=2)
    print(f"[ATTR] wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
