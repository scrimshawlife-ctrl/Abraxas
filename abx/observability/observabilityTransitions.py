from __future__ import annotations

from abx.observability.types import ObservabilityTransitionRecord


def build_observability_transition_records() -> list[ObservabilityTransitionRecord]:
    return [
        ObservabilityTransitionRecord("obtr.001", "queue.retry.path", "COVERAGE_PARTIAL", "PARTIAL_VISIBILITY_ACTIVE", "retry spans missing"),
        ObservabilityTransitionRecord("obtr.002", "identity.merge.path", "COVERAGE_DEGRADED", "INSTRUMENTATION_STALE", "merge traces outdated"),
        ObservabilityTransitionRecord("obtr.003", "approval.override.path", "MEASUREMENT_AMBIGUOUS", "FALSE_ASSURANCE_RISK", "alerts not consequence-aware"),
        ObservabilityTransitionRecord("obtr.004", "runtime.latency.path", "COVERAGE_PARTIAL", "TRUST_RESTORED", "new metrics validated"),
        ObservabilityTransitionRecord("obtr.005", "edge.delivery.path", "COVERAGE_UNKNOWN", "BLOCKED", "telemetry channel down"),
    ]
