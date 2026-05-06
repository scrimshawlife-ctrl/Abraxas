#!/usr/bin/env python3
"""Run Yggdrasil runtime - v2.0.2 topology runtime engine.

Emits a runtime topology packet describing the shadow execution graph
topology with route nodes, edges, and deterministic graph hash.
"""
from __future__ import annotations

import json
import sys
from hashlib import sha256
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


TOPOLOGY_NODES = [
    {"node_id": "node.audit", "role": "audit", "lane": "shadow"},
    {"node_id": "node.hash", "role": "hash", "lane": "shadow"},
    {"node_id": "node.validate", "role": "validate", "lane": "shadow"},
    {"node_id": "node.route", "role": "route", "lane": "shadow"},
]

TOPOLOGY_EDGES = [
    {"from": "node.audit", "to": "node.hash"},
    {"from": "node.hash", "to": "node.validate"},
    {"from": "node.validate", "to": "node.route"},
]


def build_topology_packet(nodes: list, edges: list) -> dict:
    """Build a deterministic topology packet."""
    canonical = json.dumps(
        {"nodes": sorted(nodes, key=lambda n: n["node_id"]),
         "edges": sorted(edges, key=lambda e: (e["from"], e["to"]))},
        sort_keys=True,
    ).encode("utf-8")
    graph_hash = sha256(canonical).hexdigest()
    return {
        "schema_version": "YggdrasilRuntimeTopology.v1",
        "node_count": len(nodes),
        "edge_count": len(edges),
        "graph_hash": graph_hash,
        "nodes": nodes,
        "edges": edges,
        "projection_only": True,
        "inference_authority": False,
    }


def main() -> None:
    out_dir = Path("out/yggdrasil")
    out_dir.mkdir(parents=True, exist_ok=True)

    packet = build_topology_packet(TOPOLOGY_NODES, TOPOLOGY_EDGES)

    out_path = out_dir / "latest.json"
    out_path.write_text(json.dumps(packet, indent=2), encoding="utf-8")

    print(f"Yggdrasil runtime topology: {packet['node_count']} nodes, "
          f"{packet['edge_count']} edges")
    print(f"  Graph hash: {packet['graph_hash'][:16]}...")
    print(f"  out/yggdrasil/latest.json")


if __name__ == "__main__":
    main()
