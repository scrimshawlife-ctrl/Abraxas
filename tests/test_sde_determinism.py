"""Tests for deterministic SDE output."""

from __future__ import annotations

import hashlib

from abraxas.sources.discovery import discover_sources


def _hash_payload(payload) -> str:
    return hashlib.sha256(str(payload).encode("utf-8")).hexdigest()


def test_sde_deterministic_candidates():
    residuals = [
        {
            "affected_vectors": ["V4_SEMANTIC_INFLATION", "V5_SLANG_MUTATION"],
            "affected_domains": ["CULTURE", "LINGUISTICS"],
            "evidence_refs": ["run_id_123", "packet_hash_abc"],
            "confidence": 0.62,
        }
    ]

    outputs = [discover_sources(residuals=residuals) for _ in range(12)]
    hashes = {_hash_payload(output) for output in outputs}
    assert len(hashes) == 1, "SDE output must be deterministic"
