from __future__ import annotations

from abx.epistemics.types import GroundTruthReferenceRecord


def build_ground_truth_references() -> list[GroundTruthReferenceRecord]:
    return [
        GroundTruthReferenceRecord(
            reference_id="ref.forecast.realized_outcomes",
            reference_surface="forecast_outcome_ledger",
            reference_class="direct_ground_truth",
            reliability="high",
            owner="forecast",
        ),
        GroundTruthReferenceRecord(
            reference_id="ref.replay.golden_fixture",
            reference_surface="test_golden_fixtures",
            reference_class="proxy_reference",
            reliability="medium",
            owner="governance",
        ),
        GroundTruthReferenceRecord(
            reference_id="ref.legacy.import_expectation",
            reference_surface="legacy_import_behavior",
            reference_class="heuristic_reference",
            reliability="low",
            owner="integration",
        ),
    ]
