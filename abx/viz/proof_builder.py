from __future__ import annotations

from typing import Any, Mapping

from abx.schemas.aal_viz_proof_state import AALVizProofState
from abx.viz.hash_resolver import resolve_source_hash


_SOURCE_LANE = {
    "calibration": "FORECAST",
    "weighting": "FORECAST",
    "fusion": "PROJECTION",
    "adversarial": "SHADOW",
}


def _review_map(operator_queue: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    items = operator_queue.get("items", []) if isinstance(operator_queue.get("items", []), list) else []
    out: dict[str, dict[str, Any]] = {}
    for row in items:
        if isinstance(row, dict):
            out[str(row.get("source_system", ""))] = row
    return out


def build_proof_states(
    report: Mapping[str, Any],
    advisory: Mapping[str, Any],
    fusion: Mapping[str, Any],
    operator_queue: Mapping[str, Any],
) -> list[AALVizProofState]:
    review_by_source = _review_map(operator_queue)
    artifacts = [
        ("calibration", "calibration_drift_report", report),
        ("weighting", "domain_weight_advisory", advisory),
        ("fusion", "fusion_projection", fusion),
    ]

    states: list[AALVizProofState] = []
    for source_system, projection_id, artifact in artifacts:
        review = review_by_source.get(source_system, {})
        review_id = str(review.get("review_id", "") or "") or None
        priority = str(review.get("priority", "") or "")

        path = f"out/pse/{projection_id}.jsonl"
        hash_value = resolve_source_hash(path, artifact=artifact)

        if hash_value == "NOT_COMPUTABLE":
            display_status = "NOT_COMPUTABLE"
            display_allowed = False
        elif priority == "P0":
            display_status = "BLOCKED"
            display_allowed = False
        else:
            display_status = "OK"
            display_allowed = True

        lane = _SOURCE_LANE.get(source_system, "SHADOW")
        states.append(
            {
                "schema_version": "AALVizProofState.v1",
                "projection_id": projection_id,
                "source_artifact_path": path,
                "source_artifact_sha256": hash_value,
                "authority_lane": lane,
                "display_status": display_status,
                "fail_closed": True,
                "display_allowed": display_allowed,
                "operator_review_item_id": review_id,
                "ui_inferred_authority_allowed": False,
            }
        )

    states.sort(key=lambda item: (item["authority_lane"], item["projection_id"]))
    return states
