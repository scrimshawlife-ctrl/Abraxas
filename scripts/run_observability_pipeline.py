#!/usr/bin/env python3
"""Run observability pipeline - v2.0.3 governed observability.

Emits an observability packet covering execution metrics, receipt
chain visibility, and replay coverage in projection-only mode.
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
    authority_id="auth.observability.001",
    actor="system.observability",
    locked=True,
    scope="shadow_only",
)

RUNE_CATALOG = {
    "RUNE_AUDIT": {"input_schema": {}, "output_schema": {}},
    "RUNE_HASH": {"input_schema": {}, "output_schema": {}},
    "RUNE_VALIDATE": {"input_schema": {}, "output_schema": {}},
}

ROUTE_GRAPH = {
    "graph_hash": "a" * 64,
    "RUNE_AUDIT": {"node": "node.audit", "edges": ["node.hash"]},
    "RUNE_HASH": {"node": "node.hash", "edges": ["node.validate"]},
    "RUNE_VALIDATE": {"node": "node.validate", "edges": []},
}

CONTRACT = {
    "pipeline_id": "pipeline.observability.v1",
    "lane": "shadow",
    "required_runes": ["RUNE_AUDIT", "RUNE_HASH", "RUNE_VALIDATE"],
    "authority": AUTHORITY,
    "metadata": {"tier": "1", "mode": "shadow_only"},
}


def build_observability_packet(
    run_status: str,
    receipt_count: int,
    replay_match: bool,
    chain_hash: str,
) -> dict:
    """Build a projection-only observability packet."""
    canonical = json.dumps(
        {
            "run_status": run_status,
            "receipt_count": receipt_count,
            "replay_match": replay_match,
            "chain_hash": chain_hash,
        },
        sort_keys=True,
    ).encode("utf-8")
    packet_hash = sha256(canonical).hexdigest()
    return {
        "schema_version": "ObservabilityPacket.v1",
        "projection_only": True,
        "inference_authority": False,
        "run_status": run_status,
        "receipt_count": receipt_count,
        "replay_deterministic_match": replay_match,
        "chain_hash_prefix": chain_hash[:16] + "...",
        "packet_hash": packet_hash,
    }


def main() -> None:
    out_dir = Path("out/observability")
    out_dir.mkdir(parents=True, exist_ok=True)

    run = run_shadow_execution(CONTRACT, ROUTE_GRAPH, RUNE_CATALOG)
    replay_pkt = replay_execution(run, CONTRACT, ROUTE_GRAPH, RUNE_CATALOG)

    packet = build_observability_packet(
        run_status=run.status,
        receipt_count=len(run.executed_steps),
        replay_match=replay_pkt.deterministic_match,
        chain_hash=run.receipt_chain_hash,
    )

    out_path = out_dir / "latest.json"
    out_path.write_text(json.dumps(packet, indent=2), encoding="utf-8")

    print(f"Observability pipeline: status={run.status}, "
          f"receipts={len(run.executed_steps)}, "
          f"replay_match={replay_pkt.deterministic_match}")
    print(f"  out/observability/latest.json")


if __name__ == "__main__":
    main()
