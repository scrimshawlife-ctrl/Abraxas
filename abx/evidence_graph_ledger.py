from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _h(s: str) -> str:
    return hashlib.sha256((s or "").encode("utf-8")).hexdigest()[:20]


def claim_id(term: str, claim_handle: str) -> str:
    return _h(f"claim|{(term or '').strip().lower()}|{(claim_handle or '').strip().lower()}")


def entity_id(entity: str) -> str:
    return _h(f"entity|{(entity or '').strip().lower()}")


def append_event(path: str, ev: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")


def add_claim(*, ledger: str, run_id: str, term: str, claim_handle: str, text: str = "", claim_type: str = "assertion") -> Dict[str, Any]:
    ev = {
        "kind": "claim_added",
        "ts": _utc_now_iso(),
        "run_id": run_id,
        "term": term,
        "claim_id": claim_id(term, claim_handle),
        "claim_handle": claim_handle,
        "claim_type": claim_type,
        "text": text or None,
        "notes": "Atomic claim node. claim_handle should be stable across runs when possible.",
    }
    append_event(ledger, ev)
    return ev


def link_anchor_to_claim(
    *,
    ledger: str,
    run_id: str,
    term: str,
    anchor_id: str,
    claim_id_: str,
    relation: str,
    weight: float = 1.0,
    primary: bool = False,
    domain: str = "",
) -> Dict[str, Any]:
    rel = relation.upper().strip()
    if rel not in ("SUPPORTS", "CONTRADICTS", "REFRAMES", "ORIGINATES"):
        rel = "SUPPORTS"
    ev = {
        "kind": "anchor_claim_link",
        "ts": _utc_now_iso(),
        "run_id": run_id,
        "term": term,
        "edge_id": _h(f"acl|{run_id}|{anchor_id}|{claim_id_}|{rel}"),
        "anchor_id": anchor_id,
        "claim_id": claim_id_,
        "relation": rel,
        "weight": float(weight),
        "primary": bool(primary),
        "domain": domain or None,
        "notes": "Evidence edge: anchor ↔ claim with signed relation.",
    }
    append_event(ledger, ev)
    return ev


def add_claim_edge(*, ledger: str, run_id: str, term: str, src_claim_id: str, dst_claim_id: str, relation: str) -> Dict[str, Any]:
    rel = relation.upper().strip()
    if rel not in ("SUPPORTS", "CONTRADICTS", "REFRAMES", "DERIVES"):
        rel = "DERIVES"
    ev = {
        "kind": "claim_edge",
        "ts": _utc_now_iso(),
        "run_id": run_id,
        "term": term,
        "edge_id": _h(f"ce|{run_id}|{src_claim_id}|{dst_claim_id}|{rel}"),
        "src_claim_id": src_claim_id,
        "dst_claim_id": dst_claim_id,
        "relation": rel,
        "notes": "Claim-to-claim relation: support/contradict/reframe/derive.",
    }
    append_event(ledger, ev)
    return ev


def link_entity(*, ledger: str, run_id: str, term: str, node_kind: str, node_id: str, entity: str, relation: str = "MENTIONS") -> Dict[str, Any]:
    nk = node_kind.upper().strip()
    rel = relation.upper().strip()
    if nk not in ("TERM", "CLAIM"):
        nk = "CLAIM"
    if rel not in ("MENTIONS", "ABOUT", "TARGETS", "BENEFITS", "HARMS"):
        rel = "MENTIONS"
    ev = {
        "kind": "entity_linked",
        "ts": _utc_now_iso(),
        "run_id": run_id,
        "term": term,
        "edge_id": _h(f"el|{run_id}|{nk}|{node_id}|{entity}|{rel}"),
        "node_kind": nk,
        "node_id": node_id,
        "entity_id": entity_id(entity),
        "entity": entity,
        "relation": rel,
        "notes": "Entity association (weak semantic grounding).",
    }
    append_event(ledger, ev)
    return ev


def main() -> int:
    ap = argparse.ArgumentParser(description="Evidence graph ledger writer")
    ap.add_argument("--ledger", default="out/ledger/evidence_graph.jsonl")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("add-claim")
    c.add_argument("--run-id", required=True)
    c.add_argument("--term", required=True)
    c.add_argument("--claim-handle", required=True)
    c.add_argument("--text", default="")
    c.add_argument("--claim-type", default="assertion")

    l = sub.add_parser("link-anchor")
    l.add_argument("--run-id", required=True)
    l.add_argument("--term", required=True)
    l.add_argument("--anchor-id", required=True)
    l.add_argument("--claim-id", required=True)
    l.add_argument("--relation", required=True)
    l.add_argument("--weight", type=float, default=1.0)
    l.add_argument("--primary", action="store_true")
    l.add_argument("--domain", default="")

    ce = sub.add_parser("claim-edge")
    ce.add_argument("--run-id", required=True)
    ce.add_argument("--term", required=True)
    ce.add_argument("--src-claim-id", required=True)
    ce.add_argument("--dst-claim-id", required=True)
    ce.add_argument("--relation", required=True)

    el = sub.add_parser("link-entity")
    el.add_argument("--run-id", required=True)
    el.add_argument("--term", required=True)
    el.add_argument("--node-kind", required=True)
    el.add_argument("--node-id", required=True)
    el.add_argument("--entity", required=True)
    el.add_argument("--relation", default="MENTIONS")

    args = ap.parse_args()

    if args.cmd == "add-claim":
        ev = add_claim(ledger=args.ledger, run_id=args.run_id, term=args.term, claim_handle=args.claim_handle, text=args.text, claim_type=args.claim_type)
        print(f"[EVID_GRAPH] claim_added claim_id={ev['claim_id']}")
        return 0
    if args.cmd == "link-anchor":
        ev = link_anchor_to_claim(ledger=args.ledger, run_id=args.run_id, term=args.term, anchor_id=args.anchor_id, claim_id_=args.claim_id, relation=args.relation, weight=float(args.weight), primary=bool(args.primary), domain=args.domain)
        print(f"[EVID_GRAPH] anchor_claim_link edge_id={ev['edge_id']}")
        return 0
    if args.cmd == "claim-edge":
        ev = add_claim_edge(ledger=args.ledger, run_id=args.run_id, term=args.term, src_claim_id=args.src_claim_id, dst_claim_id=args.dst_claim_id, relation=args.relation)
        print(f"[EVID_GRAPH] claim_edge edge_id={ev['edge_id']}")
        return 0
    if args.cmd == "link-entity":
        ev = link_entity(ledger=args.ledger, run_id=args.run_id, term=args.term, node_kind=args.node_kind, node_id=args.node_id, entity=args.entity, relation=args.relation)
        print(f"[EVID_GRAPH] entity_linked edge_id={ev['edge_id']}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
