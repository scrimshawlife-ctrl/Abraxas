from __future__ import annotations

from abx.performance.types import ThroughputConstraintRecord


def build_throughput_constraints() -> list[ThroughputConstraintRecord]:
    return [
        ThroughputConstraintRecord(
            record_id="thr.scheduler.queue_depth",
            surface_id="core.runtime_orchestrator.dispatch",
            constraint_type="queue_depth",
            scope="run",
            status="governed",
            evidence="deterministic_dispatch_batch",
        ),
        ThroughputConstraintRecord(
            record_id="thr.validation.serial_gate",
            surface_id="core.execution_validator.validate",
            constraint_type="serial_validation",
            scope="workflow",
            status="governed",
            evidence="proof_integrity_gate",
        ),
        ThroughputConstraintRecord(
            record_id="thr.interop.rate_limit",
            surface_id="interop.federation.handoff",
            constraint_type="remote_rate_limit",
            scope="environment",
            status="monitored",
            evidence="adapter_remote_limit",
        ),
    ]


def classify_throughput_constraints() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {"governed": [], "monitored": [], "partial": []}
    for row in build_throughput_constraints():
        out[row.status].append(row.record_id)
    return {k: sorted(v) for k, v in out.items()}
