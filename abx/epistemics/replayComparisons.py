from __future__ import annotations

from abx.epistemics.types import ReplayComparisonRecord


def build_replay_comparisons() -> list[ReplayComparisonRecord]:
    return [
        ReplayComparisonRecord(
            comparison_id="cmp.runtime.replay_consistency",
            replay_surface="cycle_runner_replay",
            live_surface="cycle_runner_live",
            mismatch_class="none",
            status="replay_consistency_only",
        ),
        ReplayComparisonRecord(
            comparison_id="cmp.forecast.outcome_delta",
            replay_surface="forecast_replay",
            live_surface="forecast_live",
            mismatch_class="within_tolerance",
            status="proxy_alignment",
        ),
        ReplayComparisonRecord(
            comparison_id="cmp.legacy.import_delta",
            replay_surface="legacy_import_replay",
            live_surface="legacy_import_live",
            mismatch_class="semantic_drift",
            status="heuristic_comparison",
        ),
    ]
