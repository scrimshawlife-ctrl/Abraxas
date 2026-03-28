from __future__ import annotations


def build_coverage_inventory() -> tuple[tuple[str, str, str, str], ...]:
    return (
        ("cov.001", "runtime.latency.path", "COVERAGE_SUFFICIENT", "METRICS_TRACES_LOGS"),
        ("cov.002", "queue.retry.path", "COVERAGE_PARTIAL", "METRICS_ONLY"),
        ("cov.003", "identity.merge.path", "COVERAGE_DEGRADED", "LOGS_ONLY"),
        ("cov.004", "approval.override.path", "NO_MEANINGFUL_COVERAGE", "SPARSE_EVENTS"),
        ("cov.005", "capacity.exhaustion.path", "COVERAGE_UNKNOWN", "UNKNOWN"),
        ("cov.006", "edge.delivery.path", "NOT_COMPUTABLE", "TELEMETRY_UNAVAILABLE"),
    )
