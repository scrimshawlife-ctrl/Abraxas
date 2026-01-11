"""Tests for TVM schema determinism and serialization stability."""

from __future__ import annotations

from abraxas.schema.tvm import build_tvm_frame, hash_tvm_frame


def test_tvm_serialization_stable_across_reruns():
    observation = {
        "domain": "astrology",
        "timestamp_utc": "2025-06-01T00:00:00Z",
        "vectors": {
            "V1_SIGNAL_DENSITY": 0.42,
            "V8_EMOTIONAL_CLIMATE": 0.66,
            "V13_ARCHETYPAL_ACTIVATION": 0.71,
        },
        "sources": ["https://www.weforum.org/reports/global-risks-report-2025/"],
        "assumptions": ["symbolic_domain_seed"],
    }

    frame = build_tvm_frame(observation, run_id="test_run")
    hashes = {hash_tvm_frame(frame) for _ in range(12)}
    assert len(hashes) == 1, "TVM serialization hash must be stable across reruns"
