#!/usr/bin/env python3
"""Run deterministic shadow execution for a Tier-1 pipeline."""
from __future__ import annotations
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.models.governance import Authority
from core.execution.shadow_runner import run_shadow_execution

TIER1_PIPELINE = "pipeline.tier1.v1"

AUTHORITY = Authority(
    authority_id="auth.shadow.001",
    actor="system.shadow",
    locked=True,
    scope="shadow_only",
)

RUNE_CATALOG = {
    "RUNE_AUDIT": {
        "input_schema": {"type": "object"},
        "output_schema": {"type": "object"},
    },
    "RUNE_HASH": {
        "input_schema": {"type": "object"},
        "output_schema": {"type": "object"},
    },
    "RUNE_VALIDATE": {
        "input_schema": {"type": "object"},
        "output_schema": {"type": "object"},
    },
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
    out_dir = Path("out/execution")
    out_dir.mkdir(parents=True, exist_ok=True)

    run = run_shadow_execution(CONTRACT, ROUTE_GRAPH, RUNE_CATALOG)
    run_dict = {
        "schema_version": run.schema_version,
        "run_id": run.run_id,
        "pipeline_id": run.pipeline_id,
        "execution_context_hash": run.execution_context_hash,
        "invocation_plan_hash": run.invocation_plan_hash,
        "receipt_chain_hash": run.receipt_chain_hash,
        "executed_steps": run.executed_steps,
        "failed_steps": run.failed_steps,
        "skipped_steps": run.skipped_steps,
        "status": run.status,
        "recommended_next_state": run.recommended_next_state,
    }
    (out_dir / "latest.json").write_text(json.dumps(run_dict, indent=2), encoding="utf-8")

    receipts_data = {
        "run_id": run.run_id,
        "receipt_chain_hash": run.receipt_chain_hash,
        "executed_steps": run.executed_steps,
    }
    (out_dir / "receipts.latest.json").write_text(
        json.dumps(receipts_data, indent=2), encoding="utf-8"
    )

    print(f"Shadow execution complete: status={run.status}")
    print(f"  out/execution/latest.json")
    print(f"  out/execution/receipts.latest.json")


if __name__ == "__main__":
    main()
