"""Deterministic linguistic feature extraction tests."""

from __future__ import annotations

from abraxas.metric_extractors.linguistics import LinguisticsExtractor


def test_linguistic_features_stable():
    extractor = LinguisticsExtractor()
    packets = [
        {
            "source_id": "LINGUISTIC_NEWS",
            "observed_at_utc": "2025-01-01T00:00:00Z",
            "window_start_utc": "2025-01-01T00:00:00Z",
            "window_end_utc": "2025-01-01T01:00:00Z",
            "payload": {
                "items": [
                    {"text": "AI is good but then AI is evil", "ts_utc": "2025-01-01T00:00:00Z"}
                ]
            },
        }
    ]
    metrics = extractor.extract(packets, {})
    metric_ids = {point.metric_id for point in metrics}
    assert "linguistics.token_count_total" in metric_ids
    assert "linguistics.story_arc_marker_rate" in metric_ids
