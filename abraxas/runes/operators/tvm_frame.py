"""ABX-Rune Operator: TVM_FRAME."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.metric_extractors.base import MetricPoint
from abraxas.tvm.frame import compose_frames_by_domain


class TVMFrameResult(BaseModel):
    shadow_only: bool = Field(True, description="Shadow-only enforcement")
    frames: List[Dict[str, Any]] = Field(default_factory=list)
    not_computable_detail: Optional[Dict[str, Any]] = Field(
        None, description="Structured not_computable detail"
    )
    provenance: Dict[str, Any] = Field(default_factory=dict)


def apply_tvm_frame(
    metrics: List[Dict[str, Any]],
    *,
    window_start_utc: str,
    window_end_utc: str,
    strict_execution: bool = False,
) -> Dict[str, Any]:
    if metrics is None:
        if strict_execution:
            raise NotImplementedError("TVM_FRAME requires metrics")
        provenance = {
            "inputs_hash": sha256_hex(canonical_json([])),
            "frame_hashes": [],
        }
        return TVMFrameResult(
            frames=[],
            not_computable_detail={
                "reason": "missing required inputs",
                "missing_inputs": ["metrics"],
            },
            provenance=provenance,
        ).model_dump()

    points = [MetricPoint(**metric) for metric in metrics]
    frames = compose_frames_by_domain(points, window_start_utc=window_start_utc, window_end_utc=window_end_utc)
    payload = [frame.model_dump() for frame in frames]
    provenance = {
        "inputs_hash": sha256_hex(canonical_json(metrics or [])),
        "frame_hashes": [frame.frame_hash() for frame in frames],
    }
    return TVMFrameResult(frames=payload, provenance=provenance).model_dump()
