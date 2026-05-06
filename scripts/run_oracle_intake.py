#!/usr/bin/env python3
"""Run oracle intake - v2.0.6 governed oracle intake pipeline.

Behavior:
- loads deterministic source fixtures
- runs oracle intake pipeline
- emits intake artifacts

Writes:
  out/oracle/latest.json
  out/intake_conflicts/latest.json
  out/intake_approvals/latest.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.models.governance import Authority
from core.oracle.runtime import run_oracle_intake

AUTHORITY = Authority(
    authority_id="auth.oracle_intake.001",
    actor="system.oracle_intake",
    locked=True,
    scope="oracle_intake_only",
)

# Deterministic source fixtures
FIXTURE_PAYLOADS = [
    {
        "source_id": "src-doc-001",
        "source_type": "document",
        "payload": {
            "title": "Intake Document Alpha",
            "content": "Structured evidence content A",
            "version": 1,
        },
    },
    {
        "source_id": "src-receipt-001",
        "source_type": "receipt",
        "payload": {
            "receipt_id": "rcpt-001",
            "operation": "shadow_execution",
            "hash": "a" * 64,
        },
    },
    {
        "source_id": "src-topology-001",
        "source_type": "topology",
        "payload": {
            "node_count": 3,
            "edge_count": 2,
            "topology_hash": "b" * 64,
        },
    },
]


def main() -> None:
    run_id = "oracle-intake-fixture-run-001"

    oracle_run = run_oracle_intake(
        source_payloads=FIXTURE_PAYLOADS,
        authority=AUTHORITY,
        run_id=run_id,
    )

    # Build and write lineage artifact from intake envelopes
    from core.oracle.lineage import IntakeLineageNode, build_intake_lineage
    lineage_nodes = []
    prev_hash = None
    for i, env in enumerate(oracle_run.intake_envelopes):
        node = IntakeLineageNode(
            intake_hash=env.get("raw_payload_hash", f"env_{i}"),
            parent_hash=prev_hash,
            generation=i,
        )
        lineage_nodes.append(node)
        prev_hash = node.intake_hash

    lineage_pkt = build_intake_lineage(
        lineage_id=f"{run_id}-lineage",
        lineage_nodes=lineage_nodes,
        authority=AUTHORITY,
    )

    import json
    from pathlib import Path
    lineage_dir = Path("out/intake_lineage")
    lineage_dir.mkdir(parents=True, exist_ok=True)
    lineage_data = {
        "schema_version": lineage_pkt.schema_version,
        "lineage_id": lineage_pkt.lineage_id,
        "lineage_depth": lineage_pkt.lineage_depth,
        "deterministic_lineage_hash": lineage_pkt.deterministic_lineage_hash,
        "status": lineage_pkt.status,
    }
    (lineage_dir / "latest.json").write_text(json.dumps(lineage_data, indent=2), encoding="utf-8")

    print(f"Oracle intake complete:")
    print(f"  Run ID: {oracle_run.run_id}")
    print(f"  Intake envelopes: {len(oracle_run.intake_envelopes)}")
    print(f"  Evidence packets: {len(oracle_run.evidence_packets)}")
    print(f"  Normalization packets: {len(oracle_run.normalization_packets)}")
    print(f"  Replay packets: {len(oracle_run.replay_packets)}")
    print(f"  Conflict packets: {len(oracle_run.conflict_packets)}")
    print(f"  Stabilization packets: {len(oracle_run.stabilization_packets)}")
    print(f"  Approval packets: {len(oracle_run.approval_packets)}")
    print(f"  Lineage depth: {lineage_pkt.lineage_depth}")
    print(f"  Run hash: {oracle_run.deterministic_run_hash[:16]}...")
    print(f"  Status: {oracle_run.status}")
    print(f"  out/oracle/latest.json")
    print(f"  out/intake_conflicts/latest.json")
    print(f"  out/intake_approvals/latest.json")
    print(f"  out/intake_stabilization/latest.json")
    print(f"  out/intake_lineage/latest.json")


if __name__ == "__main__":
    main()
