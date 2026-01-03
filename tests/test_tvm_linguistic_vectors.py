"""Ensure V1–V6 compute when linguistic metrics are present."""

from __future__ import annotations

from abraxas.metric_extractors.linguistics import LinguisticsExtractor
from abraxas.tvm.frame import compose_frames


def test_tvm_v1_v6_computable_with_linguistics():
    packets = [
        {
            "source_id": "LINGUISTIC_NEWS",
            "observed_at_utc": "2025-01-01T00:00:00Z",
            "window_start_utc": "2025-01-01T00:00:00Z",
            "window_end_utc": "2025-01-01T01:00:00Z",
            "payload": {
                "items": [
                    {"text": "then we act now", "ts_utc": "2025-01-01T00:00:00Z"}
                ]
            },
        }
    ]
    extractor = LinguisticsExtractor()
    points = extractor.extract(packets, {})
    frame = compose_frames(points, window_start_utc="2025-01-01T00:00:00Z", window_end_utc="2025-01-08T00:00:00Z")

    for vid in [
        "V1_SIGNAL_DENSITY",
        "V2_SIGNAL_INTEGRITY",
        "V3_DISTRIBUTION_DYNAMICS",
        "V4_SEMANTIC_INFLATION",
        "V5_SLANG_MUTATION",
        "V6_NARRATIVE_LOAD",
    ]:
        assert frame.vectors[vid].computability == "computed"
