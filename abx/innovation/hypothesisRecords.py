from __future__ import annotations

from abx.innovation.types import HypothesisRecord


def build_hypothesis_records() -> list[HypothesisRecord]:
    return [
        HypothesisRecord(
            hypothesis_id="hyp-routing-confidence",
            experiment_id="exp-hypothesis-routing-v2",
            statement="Structured route priors reduce override churn without lowering decision quality.",
            expected_signal="override_rate_down_and_quality_stable",
            baseline_ref="decision-routing-v1",
            success_criteria=["override_rate<=0.12", "quality_drift<=0.00"],
        ),
        HypothesisRecord(
            hypothesis_id="hyp-latency-window",
            experiment_id="exp-latency-compression-3",
            statement="Adaptive batching lowers p95 latency while maintaining throughput.",
            expected_signal="p95_down_throughput_steady",
            baseline_ref="runtime-batching-v2",
            success_criteria=["p95_ms<=120", "throughput_delta>=-0.03"],
        ),
        HypothesisRecord(
            hypothesis_id="hyp-memory-bridge",
            experiment_id="exp-symbolic-memory-bridge",
            statement="Context bridge improves recall continuity in long sessions.",
            expected_signal="continuity_recall_up",
            baseline_ref="continuity-v1",
            success_criteria=["continuity_gain>=0.08"],
        ),
    ]
