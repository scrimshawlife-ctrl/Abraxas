#!/usr/bin/env python3
"""Run lineage validation - v2.0.3 governed lineage tracking.

Validates execution lineage chains for determinism and emits
a lineage validation packet.
"""
from __future__ import annotations

import json
import sys
from hashlib import sha256
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.models.governance import Authority
from core.execution.shadow_runner import run_shadow_execution
from core.execution.replay_runner import replay_execution

AUTHORITY = Authority(
    authority_id="auth.lineage.001",
    actor="system.lineage",
    locked=True,
    scope="shadow_only",
)

RUNE_CATALOG = {
    "RUNE_AUDIT": {"input_schema": {}, "output_schema": {}},
    "RUNE_HASH": {"input_schema": {}, "output_schema": {}},
    "RUNE_VALIDATE": {"input_schema": {}, "output_schema": {}},
}

ROUTE_GRAPH = {
    "graph_hash": "b" * 64,
    "RUNE_AUDIT": {"node": "node.audit", "edges": ["node.hash"]},
    "RUNE_HASH": {"node": "node.hash", "edges": ["node.validate"]},
    "RUNE_VALIDATE": {"node": "node.validate", "edges": []},
}

CONTRACT = {
    "pipeline_id": "pipeline.lineage.v1",
    "lane": "shadow",
    "required_runes": ["RUNE_AUDIT", "RUNE_HASH", "RUNE_VALIDATE"],
    "authority": AUTHORITY,
    "metadata": {"tier": "1", "mode": "shadow_only"},
}


def build_lineage_packet(
    run_id: str,
    plan_hash: str,
    chain_hash: str,
    replay_match: bool,
) -> dict:
    """Build a lineage validation packet."""
    canonical = json.dumps(
        {
            "run_id": run_id,
            "plan_hash": plan_hash,
            "chain_hash": chain_hash,
            "replay_match": replay_match,
        },
        sort_keys=True,
    ).encode("utf-8")
    lineage_hash = sha256(canonical).hexdigest()
    return {
        "schema_version": "LineageValidationPacket.v1",
        "run_id": run_id,
        "plan_hash_prefix": plan_hash[:16] + "...",
        "chain_hash_prefix": chain_hash[:16] + "...",
        "replay_deterministic_match": replay_match,
        "lineage_hash": lineage_hash,
        "status": "valid" if replay_match else "invalid",
    }


def main() -> None:
    out_dir = Path("out/lineage")
    out_dir.mkdir(parents=True, exist_ok=True)

    run = run_shadow_execution(CONTRACT, ROUTE_GRAPH, RUNE_CATALOG)
    replay_pkt = replay_execution(run, CONTRACT, ROUTE_GRAPH, RUNE_CATALOG)

    packet = build_lineage_packet(
        run_id=run.run_id,
        plan_hash=run.invocation_plan_hash,
        chain_hash=run.receipt_chain_hash,
        replay_match=replay_pkt.deterministic_match,
    )

    out_path = out_dir / "latest.json"
    out_path.write_text(json.dumps(packet, indent=2), encoding="utf-8")

    print(f"Lineage validation: status={packet['status']}, "
          f"replay_match={replay_pkt.deterministic_match}")
    print(f"  Lineage hash: {packet['lineage_hash'][:16]}...")
    print(f"  out/lineage/latest.json")


if __name__ == "__main__":
    main()
