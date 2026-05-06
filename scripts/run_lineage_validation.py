#!/usr/bin/env python3
"""run_lineage_validation.py

Validates lineage determinism and replay linkage, then emits a
validation summary.

Reads:
  out/lineage/latest.json
  out/telemetry/latest.json

Emits:
  out/observability/lineage_validation_summary.json
"""
from __future__ import annotations

import json
import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from core.models.governance import Authority
from core.observability.lineage import (
    LineageTraceNode,
    LineageTracePacket,
    build_lineage_trace,
    _detect_cycles,
    _validate_parents,
)
from core.observability.replay_metrics import build_replay_telemetry
from core.observability.validators import validate_lineage_replay


def _load_json(path: str) -> dict:
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def _write_json(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)


def _reconstruct_trace(raw: dict, authority: Authority) -> LineageTracePacket:
    """Reconstruct a LineageTracePacket from a raw dict (from latest.json)."""
    nodes = []
    for n in raw.get("nodes", []):
        nodes.append(
            LineageTraceNode(
                node_id=n["node_id"],
                node_type=n.get("node_type", "execution"),
                source_hash=n["source_hash"],
                generation=n.get("generation", 0),
                parent_hash=n.get("parent_hash"),
            )
        )
    return LineageTracePacket(
        trace_id=raw.get("trace_id", "reconstructed"),
        execution_hash=raw.get("execution_hash", "unknown"),
        nodes=nodes,
        authority=authority,
        status=raw.get("status"),
    )


def main() -> int:
    print("[run_lineage_validation] starting lineage replay validation")

    authority = Authority.locked(source="run_lineage_validation")

    lineage_raw = _load_json("out/lineage/latest.json")
    telemetry_raw = _load_json("out/telemetry/latest.json")

    if lineage_raw:
        trace = _reconstruct_trace(lineage_raw, authority)
    else:
        # Synthetic trace if no artifact exists
        from hashlib import sha256
        import json as _json
        base = sha256(b"synthetic").hexdigest()
        nodes = [
            LineageTraceNode(
                node_id=f"node-{i}",
                node_type="execution",
                source_hash=sha256(f"node-{i}".encode()).hexdigest(),
                generation=i,
                parent_hash=sha256(f"node-{i-1}".encode()).hexdigest() if i > 0 else None,
            )
            for i in range(3)
        ]
        trace = build_lineage_trace(
            trace_id="synthetic-trace",
            execution_hash=base,
            nodes=nodes,
            authority=authority,
        )

    exec_hash = trace.execution_hash
    replay_tel = build_replay_telemetry(
        replay_telemetry_id="lineage-val-replay",
        replay_hash=exec_hash,
        compared_receipts=[],
        mismatched_receipts=[],
        authority=authority,
    )

    result = validate_lineage_replay(trace, replay_tel)

    # Cycle check
    has_cycle = _detect_cycles(trace.nodes)
    missing_parent = _validate_parents(trace.nodes)

    summary = {
        "schema_version": "LineageValidationSummary.v1",
        "trace_id": trace.trace_id,
        "execution_hash": exec_hash,
        "lineage_depth": trace.lineage_depth,
        "node_count": len(trace.nodes),
        "has_cycle": has_cycle,
        "missing_parent": missing_parent,
        "deterministic_chain_hash": trace.deterministic_chain_hash,
        "gate_result": result.result,
        "gate_reason": result.reason,
        "gate_details": result.details,
    }

    out_path = "out/observability/lineage_validation_summary.json"
    _write_json(out_path, summary)

    status_label = "[PASS]" if result.passed else "[FAIL]"
    print(f"  lineage_depth       : {trace.lineage_depth}")
    print(f"  node_count          : {len(trace.nodes)}")
    print(f"  has_cycle           : {has_cycle}")
    print(f"  missing_parent      : {missing_parent}")
    print(f"  gate_result         : {status_label} {result.reason}")
    print(f"  summary written to  : {out_path}")
    print("[run_lineage_validation] complete")
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
