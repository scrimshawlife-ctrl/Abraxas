"""Topology observability runner — aggregation pipeline.

run_observability_pipeline aggregates all observability packets and
emits artifacts to out/observability/, out/lineage/, out/timelines/,
and out/telemetry/.
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, List, Optional

from core.models.governance import Authority
from core.observability.telemetry import ExecutionTelemetryPacket, build_telemetry_packet
from core.observability.lineage import (
    LineageTraceNode,
    LineageTracePacket,
    build_lineage_trace,
)
from core.observability.timelines import (
    RuntimeTimelineEvent,
    RuntimeTimelinePacket,
    build_runtime_timeline,
)
from core.observability.stabilization import StabilizationTelemetry, build_stabilization_telemetry
from core.observability.metrics import MetricPoint, DeterministicMetricSeries, build_metric_series
from core.observability.replay_metrics import ReplayTelemetryPacket, build_replay_telemetry
from core.observability.snapshots import ProjectionStateSnapshot, build_projection_snapshot
from core.observability.validators import run_all_doctrine_gates


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _write_artifact(path: str, data: dict) -> None:
    """Write artifact JSON to path, creating parent dirs."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)


def _default_execution_run(run_id: str = "default-run") -> Dict[str, Any]:
    """Produce a minimal synthetic execution run descriptor."""
    base = _sha256(run_id)
    return {
        "run_id": run_id,
        "execution_run_hash": base,
        "graph_hash": _sha256(f"{run_id}:graph"),
        "traversal_hash": _sha256(f"{run_id}:traversal"),
        "scheduler_hash": _sha256(f"{run_id}:scheduler"),
        "receipt_chain_hash": _sha256(f"{run_id}:receipts"),
        "executed_node_count": 4,
        "blocked_node_count": 0,
        "failed_node_count": 0,
        "nodes": [
            {"node_id": f"node-{i}", "node_type": "execution", "source_hash": _sha256(f"{run_id}:node-{i}"), "generation": i}
            for i in range(3)
        ],
        "events": [
            {"sequence": i, "event_type": "node_executed", "source_hash": _sha256(f"{run_id}:event-{i}"), "status": "completed"}
            for i in range(4)
        ],
    }


def run_observability_pipeline(
    execution_run: Optional[Dict[str, Any]] = None,
    replay_packet: Optional[ReplayTelemetryPacket] = None,
    graph_packet: Optional[Dict[str, Any]] = None,
    *,
    out_dir: str = "out",
    run_id: str = "observability-run",
    authority: Optional[Authority] = None,
) -> Dict[str, Any]:
    """Aggregate observability, emit artifacts, return summary.

    Parameters
    ----------
    execution_run   Dict describing the execution run (or None for synthetic)
    replay_packet   Pre-built ReplayTelemetryPacket (or None for synthetic)
    graph_packet    Dict describing graph topology (or None for synthetic)
    out_dir         Root output directory (default: "out")
    run_id          Identifier for this pipeline run
    authority       Locked Authority token (creates default if None)

    Writes:
        <out_dir>/observability/latest.json
        <out_dir>/lineage/latest.json
        <out_dir>/timelines/latest.json
        <out_dir>/telemetry/latest.json
    """
    if authority is None:
        authority = Authority.locked()
    if not authority.is_locked():
        raise ValueError("authority must be locked")

    if execution_run is None:
        execution_run = _default_execution_run(run_id)

    exec_hash = execution_run.get("execution_run_hash") or _sha256(run_id)

    # ── 1. Build ExecutionTelemetryPacket ──────────────────────────────────
    telemetry = build_telemetry_packet(
        telemetry_id=f"tel-{run_id}",
        execution_run_hash=exec_hash,
        graph_hash=execution_run.get("graph_hash") or _sha256(f"{run_id}:graph"),
        traversal_hash=execution_run.get("traversal_hash") or _sha256(f"{run_id}:traversal"),
        scheduler_hash=execution_run.get("scheduler_hash") or _sha256(f"{run_id}:scheduler"),
        receipt_chain_hash=execution_run.get("receipt_chain_hash") or _sha256(f"{run_id}:receipts"),
        executed_node_count=execution_run.get("executed_node_count", 0),
        blocked_node_count=execution_run.get("blocked_node_count", 0),
        failed_node_count=execution_run.get("failed_node_count", 0),
        authority=authority,
        replay_hash=replay_packet.replay_hash if replay_packet else None,
    )

    # ── 2. Build LineageTracePacket ────────────────────────────────────────
    raw_nodes = execution_run.get("nodes", [])
    lineage_nodes: List[LineageTraceNode] = []
    for i, n in enumerate(raw_nodes):
        lineage_nodes.append(
            LineageTraceNode(
                node_id=n.get("node_id", f"node-{i}"),
                node_type=n.get("node_type", "execution"),
                source_hash=n.get("source_hash") or _sha256(f"{run_id}:node-{i}"),
                generation=n.get("generation", i),
                parent_hash=lineage_nodes[-1].source_hash if lineage_nodes else None,
            )
        )
    trace = build_lineage_trace(
        trace_id=f"trace-{run_id}",
        execution_hash=exec_hash,
        nodes=lineage_nodes,
        authority=authority,
    )

    # ── 3. Build RuntimeTimelinePacket ────────────────────────────────────
    raw_events = execution_run.get("events", [])
    timeline_events: List[RuntimeTimelineEvent] = []
    for i, ev in enumerate(raw_events):
        status = ev.get("status", "completed")
        if status not in RuntimeTimelineEvent.VALID_STATUSES:
            status = "completed"
        timeline_events.append(
            RuntimeTimelineEvent(
                sequence=ev.get("sequence", i),
                event_type=ev.get("event_type", "node_executed"),
                source_hash=ev.get("source_hash") or _sha256(f"{run_id}:event-{i}"),
                status=status,
            )
        )
    timeline = build_runtime_timeline(
        timeline_id=f"timeline-{run_id}",
        execution_hash=exec_hash,
        events=timeline_events,
        authority=authority,
    )

    # ── 4. Build StabilizationTelemetry ───────────────────────────────────
    replay_failures = 0 if (replay_packet is None or replay_packet.deterministic_match) else 1
    replay_count = 1 if replay_packet is not None else 0
    deterministic_matches = replay_count - replay_failures

    if replay_count == 0:
        stab_state = "not_started"
    elif replay_failures > 0:
        stab_state = "unstable"
    else:
        stab_state = "stable"

    stab = build_stabilization_telemetry(
        stabilization_id=f"stab-{run_id}",
        execution_hash=exec_hash,
        replay_count=replay_count,
        deterministic_replay_matches=deterministic_matches,
        replay_failures=replay_failures,
        route_failures=execution_run.get("failed_node_count", 0),
        authority=authority,
        stabilization_state=stab_state,
    )

    # ── 5. Build DeterministicMetricSeries ────────────────────────────────
    metric_points = [
        MetricPoint(
            timestamp_index=0,
            metric_name="executed_node_count",
            metric_value=float(execution_run.get("executed_node_count", 0)),
        ),
        MetricPoint(
            timestamp_index=1,
            metric_name="blocked_node_count",
            metric_value=float(execution_run.get("blocked_node_count", 0)),
        ),
        MetricPoint(
            timestamp_index=2,
            metric_name="failed_node_count",
            metric_value=float(execution_run.get("failed_node_count", 0)),
        ),
        MetricPoint(
            timestamp_index=3,
            metric_name="replay_failures",
            metric_value=float(replay_failures),
        ),
    ]
    metric_series = build_metric_series(
        series_id=f"metrics-{run_id}",
        metric_family="execution_observability",
        points=metric_points,
        authority=authority,
    )

    # ── 6. Build ReplayTelemetryPacket (synthetic if not provided) ─────────
    if replay_packet is None:
        replay_packet = build_replay_telemetry(
            replay_telemetry_id=f"replay-tel-{run_id}",
            replay_hash=exec_hash,
            compared_receipts=[],
            mismatched_receipts=[],
            authority=authority,
        )

    # ── 7. Build ProjectionStateSnapshot ──────────────────────────────────
    snapshot = build_projection_snapshot(
        snapshot_id=f"snap-{run_id}",
        projection_hash=_sha256(f"{run_id}:projection"),
        queue_hash=_sha256(f"{run_id}:queue"),
        validation_hash=_sha256(f"{run_id}:validation"),
        telemetry_hash=telemetry.packet_hash(),
        topology_hash=_sha256(f"{run_id}:topology"),
        authority=authority,
    )

    # ── 8. Run doctrine gates ──────────────────────────────────────────────
    gate_results = run_all_doctrine_gates(telemetry, trace, stab, snapshot)
    gates_passed = all(r.passed for r in gate_results)

    # ── 9. Build AAL-Viz observability_summary ─────────────────────────────
    observability_summary = {
        "execution_runs": 1,
        "replay_runs": replay_count,
        "deterministic_replays": deterministic_matches,
        "unstable_runs": 1 if stab_state == "unstable" else 0,
        "lineage_depth": trace.lineage_depth,
        "route_failures": execution_run.get("failed_node_count", 0),
        "telemetry_packets": 1,
        "stabilization_state": stab_state,
        "projection_snapshots": 1,
        "projection_only": True,
        "inference_authority": False,
    }

    # ── 10. Assemble full artifact ──────────────────────────────────────────
    pipeline_result = {
        "schema_version": "ObservabilityPipeline.v1",
        "run_id": run_id,
        "telemetry": telemetry.to_dict(),
        "lineage_trace": trace.to_dict(),
        "runtime_timeline": timeline.to_dict(),
        "stabilization": stab.to_dict(),
        "metric_series": metric_series.to_dict(),
        "replay_telemetry": replay_packet.to_dict(),
        "projection_snapshot": snapshot.to_dict(),
        "observability_summary": observability_summary,
        "doctrine_gates": [r.to_dict() for r in gate_results],
        "gates_passed": gates_passed,
    }

    # ── 11. Write artifacts ─────────────────────────────────────────────────
    _write_artifact(os.path.join(out_dir, "observability", "latest.json"), pipeline_result)
    _write_artifact(os.path.join(out_dir, "lineage", "latest.json"), trace.to_dict())
    _write_artifact(os.path.join(out_dir, "timelines", "latest.json"), timeline.to_dict())
    _write_artifact(os.path.join(out_dir, "telemetry", "latest.json"), telemetry.to_dict())

    return pipeline_result
