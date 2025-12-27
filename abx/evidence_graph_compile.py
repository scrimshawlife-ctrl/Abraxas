from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple


def _utc_now_iso() -> str:
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


def compile_graph(ledger_path: str) -> Dict[str, Any]:
    evs = _read_jsonl(ledger_path)
    nodes: Dict[str, Dict[str, Any]] = {}
    edges: List[Dict[str, Any]] = []

    def add_node(nid: str, kind: str, payload: Dict[str, Any]) -> None:
        if nid not in nodes:
            nodes[nid] = {"id": nid, "kind": kind, "payload": payload}

    for e in evs:
        k = str(e.get("kind") or "")
        if k == "claim_added":
            cid = str(e.get("claim_id") or "")
            add_node(cid, "CLAIM", {"term": e.get("term"), "claim_handle": e.get("claim_handle"), "claim_type": e.get("claim_type"), "text": e.get("text")})
        elif k == "anchor_claim_link":
            aid = str(e.get("anchor_id") or "")
            cid = str(e.get("claim_id") or "")
            add_node(aid, "ANCHOR", {"domain": e.get("domain"), "primary": e.get("primary")})
            add_node(cid, "CLAIM", {"term": e.get("term")})
            edges.append({"id": e.get("edge_id"), "kind": "ANCHOR_CLAIM", "src": aid, "dst": cid, "relation": e.get("relation"), "weight": e.get("weight"), "primary": e.get("primary"), "domain": e.get("domain"), "ts": e.get("ts"), "run_id": e.get("run_id"), "term": e.get("term")})
        elif k == "claim_edge":
            s = str(e.get("src_claim_id") or "")
            d = str(e.get("dst_claim_id") or "")
            add_node(s, "CLAIM", {"term": e.get("term")})
            add_node(d, "CLAIM", {"term": e.get("term")})
            edges.append({"id": e.get("edge_id"), "kind": "CLAIM_EDGE", "src": s, "dst": d, "relation": e.get("relation"), "ts": e.get("ts"), "run_id": e.get("run_id"), "term": e.get("term")})
        elif k == "entity_linked":
            eid = str(e.get("entity_id") or "")
            add_node(eid, "ENTITY", {"entity": e.get("entity")})
            add_node(str(e.get("node_id") or ""), str(e.get("node_kind") or "CLAIM"), {"term": e.get("term")})
            edges.append({"id": e.get("edge_id"), "kind": "ENTITY_LINK", "src": str(e.get("node_id") or ""), "dst": eid, "relation": e.get("relation"), "ts": e.get("ts"), "run_id": e.get("run_id"), "term": e.get("term")})

    return {
        "version": "evidence_graph.v0.1",
        "ts": _utc_now_iso(),
        "ledger": ledger_path,
        "n_events": len(evs),
        "nodes": list(nodes.values()),
        "edges": edges,
        "notes": "Compiled evidence graph (materialized view). Deterministic. Append-only sources.",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Compile evidence graph from ledger into a materialized graph JSON")
    ap.add_argument("--ledger", default="out/ledger/evidence_graph.jsonl")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    g = compile_graph(args.ledger)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = args.out or os.path.join("out/graphs", f"evidence_graph_{stamp}.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(g, f, ensure_ascii=False, indent=2)
    print(f"[EVID_GRAPH] wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
