#!/usr/bin/env python3
"""Run doctrine validator for the rune execution layer."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.models.governance import Authority
from core.execution.shadow_runner import run_shadow_execution
from core.runes.receipts import build_receipt_chain
from core.runes.runtime import build_invocation_plan
from core.runes.replay import RuneReplayPacket
from core.execution.replay_runner import replay_execution
from core.runes.rollback import generate_rollback_packet
from core.validators.doctrine import (
    validate_pipeline_doctrine,
    doctrine_result_to_dict,
)

TIER1_PIPELINE = "pipeline.tier1.v1"

AUTHORITY = Authority(
    authority_id="auth.shadow.001",
    actor="system.shadow",
    locked=True,
    scope="shadow_only",
)

RUNE_CATALOG = {
    "RUNE_AUDIT": {"input_schema": {"type": "object"}, "output_schema": {"type": "object"}},
    "RUNE_HASH": {"input_schema": {"type": "object"}, "output_schema": {"type": "object"}},
    "RUNE_VALIDATE": {"input_schema": {"type": "object"}, "output_schema": {"type": "object"}},
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
    out_dir = Path("out/validators")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Build invocation plan evidence
    plan = build_invocation_plan(CONTRACT, ROUTE_GRAPH, RUNE_CATALOG)
    plan_dict = {
        "schema_version": plan.schema_version,
        "plan_id": plan.plan_id,
        "pipeline_id": plan.pipeline_id,
        "steps": [
            {
                "step_id": s.step_id,
                "rune_id": s.rune_id,
                "route_node": s.route_node,
                "deterministic_order": s.deterministic_order,
                "input_schema": s.input_schema,
                "output_schema": s.output_schema,
                "required_receipts": s.required_receipts,
            }
            for s in plan.steps
        ],
    }

    # Run shadow execution and collect receipts
    run = run_shadow_execution(CONTRACT, ROUTE_GRAPH, RUNE_CATALOG)

    # Build receipt chain evidence
    receipt_chain_evidence = {
        "chain_hash": run.receipt_chain_hash,
        "receipt_count": len(run.executed_steps),
    }

    # Build replay packet evidence
    replay_pkt = replay_execution(run, CONTRACT, ROUTE_GRAPH, RUNE_CATALOG)
    replay_dict = {
        "schema_version": replay_pkt.schema_version,
        "replay_id": replay_pkt.replay_id,
        "deterministic_match": replay_pkt.deterministic_match,
        "mismatched_receipts": replay_pkt.mismatched_receipts,
        "status": replay_pkt.status,
    }

    # Build rollback packet evidence
    rollback_pkt = generate_rollback_packet(
        source_execution_id=run.run_id,
        reverted_receipts=run.executed_steps,
        reason="doctrine_validation_check",
        authority=AUTHORITY,
    )
    rollback_dict = {
        "schema_version": rollback_pkt.schema_version,
        "rollback_id": rollback_pkt.rollback_id,
        "rollback_possible": rollback_pkt.rollback_possible,
        "rollback_reason": rollback_pkt.rollback_reason,
    }

    # Run doctrine validation
    evidence = {
        "invocation_plan": plan_dict,
        "receipt_chain": receipt_chain_evidence,
        "replay_packet": replay_dict,
        "rollback_packet": rollback_dict,
    }

    result = validate_pipeline_doctrine(TIER1_PIPELINE, evidence)
    result_dict = doctrine_result_to_dict(result)

    out_path = out_dir / "doctrine_validation.latest.json"
    out_path.write_text(json.dumps(result_dict, indent=2), encoding="utf-8")

    compliant_str = "COMPLIANT" if result.fully_compliant else "NON-COMPLIANT"
    print(f"Doctrine validation: {compliant_str}")
    for gate in result.gates:
        print(f"  [{gate.status.value.upper()}] {gate.gate_id}: {gate.reason}")
    print(f"  out/validators/doctrine_validation.latest.json")


if __name__ == "__main__":
    main()
