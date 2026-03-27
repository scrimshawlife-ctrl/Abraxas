from __future__ import annotations

from abx.innovation.types import ExperimentConditionRecord


def build_experiment_conditions() -> list[ExperimentConditionRecord]:
    return [
        ExperimentConditionRecord(
            condition_id="cond-routing-a",
            experiment_id="exp-hypothesis-routing-v2",
            method="shadow_replay",
            config_ref="cfg-routing-v2-a",
            dataset_ref="replay-2026w12",
            run_envelope="sandbox",
        ),
        ExperimentConditionRecord(
            condition_id="cond-latency-a",
            experiment_id="exp-latency-compression-3",
            method="canary_5pct",
            config_ref="cfg-latency-c3",
            dataset_ref="traffic-window-2026-03",
            run_envelope="staging",
        ),
        ExperimentConditionRecord(
            condition_id="cond-memory-a",
            experiment_id="exp-symbolic-memory-bridge",
            method="paired_eval",
            config_ref="cfg-memory-bridge-v1",
            dataset_ref="continuity-suite-v2",
            run_envelope="isolated-lab",
        ),
    ]
