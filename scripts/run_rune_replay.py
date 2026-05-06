#!/usr/bin/env python3
"""Replay the latest shadow execution and emit a RuneReplayPacket."""
from __future__ import annotations
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.models.governance import Authority
from core.execution.shadow_runner import run_shadow_execution
from core.execution.replay_runner import replay_execution

TIER1_PIPELINE = "pipeline.tier1.v1"

AUTHORITY = Authority(
    authority_id="auth.shadow.001",
    actor="system.shadow",
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
    "pipeline_id": TIER1_PIPELINE,
    "lane": "shadow",
    "required_runes": ["RUNE_AUDIT", "RUNE_HASH", "RUNE_VALIDATE"],
    "authority": AUTHORITY,
    "metadata": {"tier": "1", "mode": "shadow_only"},
}


def main():
    out_dir = Path("out/replay")
    out_dir.mkdir(parents=True, exist_ok=True)

    baseline_path = Path("out/execution/latest.json")
    if not baseline_path.exists():
        print("No baseline execution found. Running first...")
        from scripts.run_shadow_execution import main as run_exec
        run_exec()

    original = run_shadow_execution(CONTRACT, ROUTE_GRAPH, RUNE_CATALOG)
    packet = replay_execution(original, CONTRACT, ROUTE_GRAPH, RUNE_CATALOG)

    packet_dict = {
        "schema_version": packet.schema_version,
        "replay_id": packet.replay_id,
        "source_execution_hash": packet.source_execution_hash,
        "replay_execution_hash": packet.replay_execution_hash,
        "identical_output": packet.identical_output,
        "deterministic_match": packet.deterministic_match,
        "mismatched_receipts": packet.mismatched_receipts,
        "status": packet.status,
    }
    (out_dir / "latest.json").write_text(
        json.dumps(packet_dict, indent=2), encoding="utf-8"
    )
    print(f"Replay complete: deterministic_match={packet.deterministic_match}")
    print(f"  out/replay/latest.json")


if __name__ == "__main__":
    main()
