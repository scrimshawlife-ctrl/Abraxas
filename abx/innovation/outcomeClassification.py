from __future__ import annotations

from abx.innovation.types import ExperimentOutcomeRecord


def build_experiment_outcomes() -> list[ExperimentOutcomeRecord]:
    return [
        ExperimentOutcomeRecord(
            outcome_id="out-routing-a",
            experiment_id="exp-hypothesis-routing-v2",
            observed_signal="override_rate=0.10, quality_drift=-0.00",
            outcome_class="promotable",
            comparison_result="better_than_baseline",
            evidence_refs=["eval:routing:2026w12"],
        ),
        ExperimentOutcomeRecord(
            outcome_id="out-latency-a",
            experiment_id="exp-latency-compression-3",
            observed_signal="p95=114ms, throughput_delta=-0.02",
            outcome_class="comparable",
            comparison_result="meets_threshold",
            evidence_refs=["perf:c3:canary:2026-03-20"],
        ),
        ExperimentOutcomeRecord(
            outcome_id="out-memory-a",
            experiment_id="exp-symbolic-memory-bridge",
            observed_signal="continuity_gain=0.03",
            outcome_class="inconclusive",
            comparison_result="below_threshold",
            evidence_refs=["cont:bridge:v1"],
        ),
        ExperimentOutcomeRecord(
            outcome_id="out-legacy-parser",
            experiment_id="exp-legacy-shadow-parser",
            observed_signal="parse_error_rate=0.21",
            outcome_class="retire_candidate",
            comparison_result="worse_than_baseline",
            evidence_refs=["ingest:legacy:shadow"],
        ),
    ]


def classify_outcome_comparability() -> dict[str, list[str]]:
    bucket: dict[str, list[str]] = {
        "promotable": [],
        "comparable": [],
        "inconclusive": [],
        "retire_candidate": [],
    }
    for rec in build_experiment_outcomes():
        bucket.setdefault(rec.outcome_class, []).append(rec.experiment_id)
    for ids in bucket.values():
        ids.sort()
    return bucket
