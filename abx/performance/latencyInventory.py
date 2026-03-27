from __future__ import annotations

from abx.performance.types import LatencyVisibilityRecord


def build_latency_visibility_inventory() -> list[LatencyVisibilityRecord]:
    return [
        LatencyVisibilityRecord(
            record_id="lat.core.dispatch",
            surface_id="core.runtime_orchestrator.dispatch",
            latency_class="core_workload_latency",
            source_kind="scheduler_dispatch",
            controllability="controllable",
            status="measured",
        ),
        LatencyVisibilityRecord(
            record_id="lat.validation.proof",
            surface_id="core.execution_validator.validate",
            latency_class="core_workload_latency",
            source_kind="validation",
            controllability="controllable",
            status="measured",
        ),
        LatencyVisibilityRecord(
            record_id="lat.observability.summary",
            surface_id="observability.summary_assembly",
            latency_class="controllable_overhead",
            source_kind="reporting",
            controllability="controllable",
            status="estimated",
        ),
        LatencyVisibilityRecord(
            record_id="lat.interop.network",
            surface_id="interop.federation.handoff",
            latency_class="unavoidable_overhead",
            source_kind="network_handoff",
            controllability="partially_controllable",
            status="heuristic",
        ),
        LatencyVisibilityRecord(
            record_id="lat.legacy.backfill",
            surface_id="legacy.batch_backfill_14d",
            latency_class="legacy_overhead",
            source_kind="historical_backfill",
            controllability="controllable",
            status="not_computable",
        ),
    ]
