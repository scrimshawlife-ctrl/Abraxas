"""Ensure V10/V11 compute when gov/econ metrics present."""

from __future__ import annotations

from abraxas.metric_extractors.economics import EconomicsExtractor
from abraxas.metric_extractors.governance import GovernanceExtractor
from abraxas.tvm.frame import compose_frames


def test_tvm_v10_v11_computable():
    econ_packet = {
        "source_id": "ECON_SERIES",
        "observed_at_utc": "2025-01-01T00:00:00Z",
        "window_start_utc": "2025-01-01T00:00:00Z",
        "window_end_utc": "2025-01-08T00:00:00Z",
        "payload": {
            "series": [
                {"ts_utc": "2025-01-01T00:00:00Z", "value": 100.0, "unit": "index", "meta": {"series_id": "cpi"}},
                {"ts_utc": "2025-01-08T00:00:00Z", "value": 102.0, "unit": "index", "meta": {"series_id": "cpi"}},
            ]
        },
    }
    gov_packet = {
        "source_id": "GOV_DOCS",
        "observed_at_utc": "2025-01-01T00:00:00Z",
        "window_start_utc": "2025-01-01T00:00:00Z",
        "window_end_utc": "2025-01-08T00:00:00Z",
        "payload": {
            "documents": [
                {"title": "Policy", "body": "Update", "ts_utc": "2025-01-01T00:00:00Z"}
            ]
        },
    }

    econ_points = EconomicsExtractor().extract([econ_packet], {})
    gov_points = GovernanceExtractor().extract([gov_packet], {})
    frame = compose_frames(econ_points + gov_points, window_start_utc="2025-01-01T00:00:00Z", window_end_utc="2025-01-08T00:00:00Z")

    assert frame.vectors["V10_GOVERNANCE_PRESSURE"].computability == "computed"
    assert frame.vectors["V11_ECONOMIC_STRESS"].computability == "computed"
