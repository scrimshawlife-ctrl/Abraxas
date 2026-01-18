"""ABX-Rune Operator: SOURCE_DISCOVER."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.sources.discovery import discover_sources


class SourceDiscoverResult(BaseModel):
    shadow_only: bool = Field(True, description="Shadow-only enforcement")
    candidates: List[Dict[str, Any]] = Field(default_factory=list)
    not_computable_detail: Optional[Dict[str, Any]] = Field(
        None, description="Structured not_computable detail"
    )
    provenance: Dict[str, Any] = Field(default_factory=dict)


def apply_source_discover(
    residuals: Optional[List[Dict[str, Any]]] = None,
    anomalies: Optional[List[Dict[str, Any]]] = None,
    convergence: Optional[List[Dict[str, Any]]] = None,
    silence: Optional[List[Dict[str, Any]]] = None,
    *,
    strict_execution: bool = False,
) -> Dict[str, Any]:
    if residuals is None and anomalies is None and convergence is None and silence is None:
        if strict_execution:
            raise NotImplementedError("SOURCE_DISCOVER requires at least one input list")
        provenance = {
            "inputs_hash": sha256_hex(
                canonical_json(
                    {
                        "residuals": [],
                        "anomalies": [],
                        "convergence": [],
                        "silence": [],
                    }
                )
            ),
            "candidate_hash": None,
        }
        return SourceDiscoverResult(
            candidates=[],
            not_computable_detail={
                "reason": "missing required inputs",
                "missing_inputs": ["residuals", "anomalies", "convergence", "silence"],
            },
            provenance=provenance,
        ).model_dump()

    output = discover_sources(
        residuals=residuals or [],
        anomalies=anomalies or [],
        convergence=convergence or [],
        silence=silence or [],
    )
    provenance = {
        "inputs_hash": sha256_hex(
            canonical_json({
                "residuals": residuals or [],
                "anomalies": anomalies or [],
                "convergence": convergence or [],
                "silence": silence or [],
            })
        ),
        "candidate_hash": output.get("provenance", {}).get("candidate_hash"),
    }
    return SourceDiscoverResult(candidates=output.get("candidates") or [], provenance=provenance).model_dump()
