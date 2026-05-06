"""v2.0.3 governed observability layer.

Provides deterministic telemetry, execution lineage tracing, topology
state timelines, replay-aware metrics, stabilization telemetry, and
projection-only operator cognition surfaces.

Hard boundaries:
- No intelligence, no LLMs, no forecasting, no autonomous behavior
- No runtime mutation, no Canon mutation, no databases
- No external APIs, no async workers
- Everything remains deterministic, replayable, receipt-backed
- Fail-closed, governance-first, projection-safe, shadow-only
"""
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
from core.observability.stabilization import (
    StabilizationTelemetry,
    build_stabilization_telemetry,
)
from core.observability.metrics import (
    MetricPoint,
    DeterministicMetricSeries,
    build_metric_series,
)
from core.observability.replay_metrics import (
    ReplayTelemetryPacket,
    build_replay_telemetry,
)
from core.observability.snapshots import (
    ProjectionStateSnapshot,
    build_projection_snapshot,
)
from core.observability.aggregation import run_observability_pipeline
from core.observability.validators import validate_lineage_replay

__all__ = [
    "ExecutionTelemetryPacket",
    "build_telemetry_packet",
    "LineageTraceNode",
    "LineageTracePacket",
    "build_lineage_trace",
    "RuntimeTimelineEvent",
    "RuntimeTimelinePacket",
    "build_runtime_timeline",
    "StabilizationTelemetry",
    "build_stabilization_telemetry",
    "MetricPoint",
    "DeterministicMetricSeries",
    "build_metric_series",
    "ReplayTelemetryPacket",
    "build_replay_telemetry",
    "ProjectionStateSnapshot",
    "build_projection_snapshot",
    "run_observability_pipeline",
    "validate_lineage_replay",
]
