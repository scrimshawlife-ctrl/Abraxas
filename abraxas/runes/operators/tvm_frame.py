"""ABX-Rune Operator: TVM_FRAME."""

from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.metric_extractors.base import MetricPoint
from abraxas.tvm.frame import compose_frames


class TVMFrameResult(BaseModel):
    shadow_only: bool = Field(True, description="Shadow-only enforcement")
    frames: List[Dict[str, Any]] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)


def apply_tvm_frame(
    metrics: List[Dict[str, Any]],
    *,
    window_start_utc: str,
    window_end_utc: str,
    strict_execution: bool = False,
) -> Dict[str, Any]:
    if strict_execution and metrics is None:
        raise NotImplementedError("TVM_FRAME requires metrics")

    points = [MetricPoint(**metric) for metric in metrics]
    frame = compose_frames(points, window_start_utc=window_start_utc, window_end_utc=window_end_utc)
    payload = frame.model_dump()
    provenance = {
        "inputs_hash": sha256_hex(canonical_json(metrics or [])),
        "frame_hash": frame.frame_hash(),
    }
    return TVMFrameResult(frames=[payload], provenance=provenance).model_dump()
