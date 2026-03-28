from __future__ import annotations

from abx.observability.types import FalseAssuranceRecord


def build_false_assurance_records() -> list[FalseAssuranceRecord]:
    return [
        FalseAssuranceRecord("fa.001", "queue.retry.path", "FALSE_ASSURANCE_RISK", "dashboard green despite retry saturation"),
        FalseAssuranceRecord("fa.002", "identity.merge.path", "OBSERVABILITY_DOWNGRADED", "critical labels dropped by parser"),
        FalseAssuranceRecord("fa.003", "approval.override.path", "CONFIDENCE_BLOCKED", "evidence too sparse for governance claim"),
        FalseAssuranceRecord("fa.004", "runtime.latency.path", "TRUST_RESTORED", "coverage and alert fidelity restored"),
    ]
