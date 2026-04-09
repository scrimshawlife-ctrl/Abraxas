from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from abraxas.contracts.oracle_trend_attachment_v1 import OracleTrendAttachmentV1


@dataclass(frozen=True)
class TrendAdapter:
    adapter_id: str = "trend"

    def build(self, *, authority: Mapping[str, Any], normalized: Mapping[str, Any]) -> Mapping[str, Any]:
        trend_inputs = list(dict(normalized.get("hashable_core", {})).get("context", {}).get("trend_inputs") or [])
        if not trend_inputs:
            return OracleTrendAttachmentV1(
                status="NOT_COMPUTABLE",
                computable=False,
                payload={"trend_state": "NOT_COMPUTABLE", "sample_count": 0},
                provenance={"source": "trend", "bounded": True},
            ).to_dict()
        vals = [float(x.get("value", 0.0)) for x in trend_inputs]
        avg = sum(vals) / float(len(vals))
        state = "up" if avg > 0 else "down" if avg < 0 else "flat"
        return OracleTrendAttachmentV1(
            status="AVAILABLE",
            computable=True,
            payload={"trend_state": state, "sample_count": len(vals), "mean_value": round(avg, 6)},
            provenance={"source": "trend", "bounded": True},
        ).to_dict()
