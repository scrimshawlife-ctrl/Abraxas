from __future__ import annotations

from abx.innovation.types import InnovationLifecycleRecord


def build_innovation_lifecycle_records() -> list[InnovationLifecycleRecord]:
    return [
        InnovationLifecycleRecord(
            lifecycle_id="life-routing",
            experiment_id="exp-hypothesis-routing-v2",
            state="promotion-ready",
            next_gate="governed_candidate",
            blockers=[],
        ),
        InnovationLifecycleRecord(
            lifecycle_id="life-latency",
            experiment_id="exp-latency-compression-3",
            state="canary-evaluated",
            next_gate="promotion_evidence",
            blockers=["security_signoff_pending"],
        ),
        InnovationLifecycleRecord(
            lifecycle_id="life-memory",
            experiment_id="exp-symbolic-memory-bridge",
            state="sandboxed",
            next_gate="prototype_evidence",
            blockers=["continuity_gain_below_target"],
        ),
        InnovationLifecycleRecord(
            lifecycle_id="life-legacy",
            experiment_id="exp-legacy-shadow-parser",
            state="stalled",
            next_gate="retire_or_rework",
            blockers=["owner_missing", "unbounded_influence"],
        ),
    ]
