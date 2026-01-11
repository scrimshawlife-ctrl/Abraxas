from abraxas.runes.operators.metric_extract import apply_metric_extract
from abraxas.runes.operators.tvm_frame import apply_tvm_frame


def test_multi_domain_frame_composition():
    window_start = "2025-01-01T00:00:00Z"
    window_end = "2025-01-08T00:00:00Z"
    packets = [
        {
            "source_id": "LINGUISTIC_TEST",
            "observed_at_utc": "2025-01-01T00:00:00Z",
            "window_start_utc": window_start,
            "window_end_utc": window_end,
            "domain": "linguistics",
            "data_grade": "real",
            "payload": {"items": [{"text": "ai must act now"}]},
        },
        {
            "source_id": "ECON_TEST",
            "observed_at_utc": "2025-01-01T00:00:00Z",
            "window_start_utc": window_start,
            "window_end_utc": window_end,
            "data_grade": "simulated",
            "payload": {
                "series": [
                    {"value": 100.0, "meta": {"series_id": "cpi"}},
                    {"value": 105.0, "meta": {"series_id": "cpi"}},
                ]
            },
        },
    ]

    metrics = apply_metric_extract(packets)["metrics"]
    metric_domains = {m["source_id"]: m["domain"] for m in metrics}
    metric_grades = {m["source_id"]: m["data_grade"] for m in metrics}

    assert metric_domains["LINGUISTIC_TEST"] == "linguistics"
    assert metric_domains["ECON_TEST"] == "economics"
    assert metric_grades["LINGUISTIC_TEST"] == "real"
    assert metric_grades["ECON_TEST"] == "simulated"

    frames = apply_tvm_frame(metrics, window_start_utc=window_start, window_end_utc=window_end)["frames"]
    assert len(frames) == 2

    frames_by_domain = {frame["domain"]: frame for frame in frames}
    assert frames_by_domain["linguistics"]["data_grade"] == "real"
    assert frames_by_domain["economics"]["data_grade"] == "simulated"
