from __future__ import annotations

from typing import Any, Dict, List, Mapping

REQUIRED_SIGNAL_SECTION_ORDER: List[str] = [
    "raw_signal",
    "structural_model",
    "optional_lenses",
    "claim_status",
    "omissions",
]


def normalize_signal_sections(payload: Mapping[str, Any]) -> Dict[str, Any]:
    normalized: Dict[str, Any] = {
        "raw_signal": dict(payload.get("raw_signal", {})) if isinstance(payload.get("raw_signal", {}), Mapping) else {},
        "structural_model": dict(payload.get("structural_model", {})) if isinstance(payload.get("structural_model", {}), Mapping) else {},
        "optional_lenses": dict(payload.get("optional_lenses", {})) if isinstance(payload.get("optional_lenses", {}), Mapping) else {},
        "claim_status": dict(payload.get("claim_status", {})) if isinstance(payload.get("claim_status", {}), Mapping) else {},
        "omissions": [],
    }
    omissions = payload.get("omissions", [])
    if isinstance(omissions, list):
        for row in omissions:
            if not isinstance(row, Mapping):
                continue
            normalized["omissions"].append(
                {
                    "omitted_by": str(row.get("omitted_by", "")),
                    "omitted_reason": str(row.get("omitted_reason", "")),
                    "boundary_type": str(row.get("boundary_type", "")),
                    "source_pointer": str(row.get("source_pointer", "")),
                }
            )
    return normalized
