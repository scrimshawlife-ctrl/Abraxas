from __future__ import annotations

from abx.observability.types import InstrumentationFreshnessRecord


def build_instrumentation_freshness_records() -> list[InstrumentationFreshnessRecord]:
    return [
        InstrumentationFreshnessRecord("fr.001", "runtime.latency.path", "INSTRUMENTATION_CURRENT", "updated in current release"),
        InstrumentationFreshnessRecord("fr.002", "queue.retry.path", "INSTRUMENTATION_STALE", "alert rules lag schema"),
        InstrumentationFreshnessRecord("fr.003", "identity.merge.path", "REFRESH_INSTRUMENTATION_REQUIRED", "missing new merge labels"),
        InstrumentationFreshnessRecord("fr.004", "approval.override.path", "INSTRUMENTATION_STALE", "override traces sampling too low"),
        InstrumentationFreshnessRecord("fr.005", "edge.delivery.path", "NOT_COMPUTABLE", "instrumentation registry unavailable"),
    ]
