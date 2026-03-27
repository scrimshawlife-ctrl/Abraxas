from __future__ import annotations

from abx.epistemics.groundTruthReferences import build_ground_truth_references
from abx.epistemics.replayComparisons import build_replay_comparisons
from abx.epistemics.types import AlignmentRecord


def build_alignment_inventory() -> list[AlignmentRecord]:
    refs = {x.reference_class: x.reference_surface for x in build_ground_truth_references()}
    return [
        AlignmentRecord(
            alignment_id="align.forecast.direct_truth",
            live_surface="forecast_live",
            reference_surface=refs["direct_ground_truth"],
            alignment_class="direct_ground_truth_alignment",
            status="aligned",
        ),
        AlignmentRecord(
            alignment_id="align.replay.proxy",
            live_surface="cycle_runner_live",
            reference_surface=refs["proxy_reference"],
            alignment_class="proxy_reference_alignment",
            status="aligned",
        ),
        AlignmentRecord(
            alignment_id="align.legacy.heuristic",
            live_surface="legacy_import_live",
            reference_surface=refs["heuristic_reference"],
            alignment_class="heuristic_alignment",
            status="drifted",
        ),
        AlignmentRecord(
            alignment_id="align.replay.only",
            live_surface="cycle_runner_live",
            reference_surface=build_replay_comparisons()[0].replay_surface,
            alignment_class="replay_consistency_only",
            status="aligned",
        ),
    ]
