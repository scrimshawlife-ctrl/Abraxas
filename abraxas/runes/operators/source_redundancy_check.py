"""ABX-Rune Operator: SOURCE_REDUNDANCY_CHECK."""

from __future__ import annotations

from itertools import combinations
from typing import Any, Dict, List

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex


class RedundancyResult(BaseModel):
    shadow_only: bool = Field(True, description="Shadow-only enforcement")
    overlaps: List[Dict[str, Any]] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)


def _coverage_vectors(source: Dict[str, Any]) -> List[str]:
    vectors = source.get("tvm_vectors")
    if vectors is None:
        coverage = source.get("coverage") or {}
        vectors = coverage.get("tvm_vectors") or []
    return sorted(set(vectors or []))


def apply_source_redundancy_check(sources: List[Dict[str, Any]], *, strict_execution: bool = False) -> Dict[str, Any]:
    if strict_execution and sources is None:
        raise NotImplementedError("SOURCE_REDUNDANCY_CHECK requires sources")

    overlaps: List[Dict[str, Any]] = []
    for a, b in combinations(sources or [], 2):
        a_vectors = set(_coverage_vectors(a))
        b_vectors = set(_coverage_vectors(b))
        shared = sorted(a_vectors & b_vectors)
        total = sorted(a_vectors | b_vectors)
        overlap_ratio = (len(shared) / len(total)) if total else 0.0
        overlaps.append(
            {
                "pair": [a.get("source_id"), b.get("source_id")],
                "shared_vectors": shared,
                "overlap_ratio": round(overlap_ratio, 6),
            }
        )

    overlaps_sorted = sorted(overlaps, key=lambda x: "::".join(x["pair"]))
    provenance = {
        "inputs_hash": sha256_hex(canonical_json({"sources": sources or []})),
        "pairs": len(overlaps_sorted),
    }
    return RedundancyResult(overlaps=overlaps_sorted, provenance=provenance).model_dump()
