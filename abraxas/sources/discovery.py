"""Shadow Source Discovery Engine (SDE) for candidate source proposals."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.schema.tvm import TVMVectorId
from abraxas.sources.types import CandidateSourceRecord, SourceKind


def _kind_from_vectors(vectors: List[str]) -> SourceKind:
    vector_set = set(vectors)
    if TVMVectorId.V4_SEMANTIC_INFLATION.value in vector_set or TVMVectorId.V5_SLANG_MUTATION.value in vector_set:
        return SourceKind.linguistic
    if TVMVectorId.V11_ECONOMIC_STRESS.value in vector_set:
        return SourceKind.economic
    if TVMVectorId.V12_TECHNICAL_CONSTRAINT.value in vector_set:
        return SourceKind.space_weather
    return SourceKind.governance


def discover_sources(
    *,
    residuals: Optional[List[Dict[str, Any]]] = None,
    anomalies: Optional[List[Dict[str, Any]]] = None,
    convergence: Optional[List[Dict[str, Any]]] = None,
    silence: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    residuals = residuals or []
    anomalies = anomalies or []
    convergence = convergence or []
    silence = silence or []

    trigger_sets = [
        ("residual_spike", residuals),
        ("vector_anomaly", anomalies),
        ("convergence_cluster", convergence),
        ("silence_detection", silence),
    ]

    candidates: List[CandidateSourceRecord] = []
    for trigger, entries in trigger_sets:
        for entry in entries:
            affected_vectors = sorted(set(entry.get("affected_vectors") or []))
            affected_domains = sorted(set(entry.get("affected_domains") or []))
            proposed_kind_value = entry.get("proposed_kind")
            if proposed_kind_value and proposed_kind_value in SourceKind._value2member_map_:
                proposed_kind = SourceKind(proposed_kind_value)
            else:
                proposed_kind = _kind_from_vectors(affected_vectors)
            provider = entry.get("proposed_provider") or "unknown_provider"
            rationale = {
                "triggers": [trigger],
                "affected_vectors": affected_vectors,
                "affected_domains": affected_domains,
                "evidence_refs": sorted(set(entry.get("evidence_refs") or [])),
            }
            estimated_coverage = {
                "vectors": affected_vectors,
                "resolution": entry.get("resolution") or "daily",
            }
            redundancy_estimate = {
                "overlaps_with": sorted(set(entry.get("overlaps_with") or [])),
                "uniqueness_score": float(entry.get("uniqueness_score", 0.5)),
            }
            provenance_plan = {
                "how_to_fetch": entry.get("how_to_fetch") or "adapter_required",
                "cache_policy": entry.get("cache_policy") or "cache_required",
                "licensing_notes": entry.get("licensing_notes") or "verify_terms",
            }
            candidate_payload = {
                "trigger": trigger,
                "provider": provider,
                "rationale": rationale,
                "estimated_coverage": estimated_coverage,
                "redundancy_estimate": redundancy_estimate,
                "provenance_plan": provenance_plan,
            }
            candidate_id = f"cand_{sha256_hex(canonical_json(candidate_payload))[:12]}"
            candidates.append(
                CandidateSourceRecord(
                    candidate_id=candidate_id,
                    proposed_kind=proposed_kind,
                    proposed_provider=provider,
                    rationale=rationale,
                    estimated_coverage=estimated_coverage,
                    redundancy_estimate=redundancy_estimate,
                    provenance_plan=provenance_plan,
                    confidence=float(entry.get("confidence", 0.55)),
                )
            )

    candidates_sorted = sorted(candidates, key=lambda c: c.candidate_id)
    payload = [candidate.model_dump() for candidate in candidates_sorted]
    return {
        "shadow_only": True,
        "candidates": payload,
        "provenance": {
            "inputs_hash": sha256_hex(canonical_json({
                "residuals": residuals,
                "anomalies": anomalies,
                "convergence": convergence,
                "silence": silence,
            })),
            "candidate_hash": sha256_hex(canonical_json(payload)),
        },
    }
