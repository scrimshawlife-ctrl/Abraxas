"""Shadow-only autopoiesis hooks for linguistic source discovery."""

from __future__ import annotations

from typing import Any, Dict, List

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.sources.types import CandidateSourceRecord, SourceKind


def propose_sources(
    *,
    tokens: List[str],
    residuals: List[Dict[str, Any]] | None = None,
    blind_spots: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    residuals = residuals or []
    blind_spots = blind_spots or []

    candidates: List[CandidateSourceRecord] = []
    if tokens:
        rationale = {
            "triggers": ["emergent_tokens"],
            "affected_vectors": [
                "V1_SIGNAL_DENSITY",
                "V4_SEMANTIC_INFLATION",
                "V5_SLANG_MUTATION",
            ],
            "affected_domains": ["LINGUISTICS"],
            "evidence_refs": [sha256_hex(canonical_json(tokens))],
        }
        payload = {
            "provider": "community_corpus",
            "rationale": rationale,
        }
        candidates.append(
            CandidateSourceRecord(
                candidate_id=f"cand_{sha256_hex(canonical_json(payload))[:12]}",
                proposed_kind=SourceKind.linguistic_meme_artifacts,
                proposed_provider="community_corpus",
                rationale=rationale,
                estimated_coverage={"vectors": rationale["affected_vectors"], "resolution": "daily"},
                redundancy_estimate={"overlaps_with": [], "uniqueness_score": 0.5},
                provenance_plan={
                    "how_to_fetch": "linguistic_jsonl",
                    "cache_policy": "required",
                    "licensing_notes": "verify_terms",
                },
                confidence=0.55,
            )
        )

    payload = [candidate.model_dump() for candidate in candidates]
    return {
        "shadow_only": True,
        "candidates": payload,
        "provenance": {
            "inputs_hash": sha256_hex(canonical_json({"tokens": tokens, "residuals": residuals, "blind_spots": blind_spots})),
        },
    }
