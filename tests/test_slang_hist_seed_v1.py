from __future__ import annotations

from abraxas.slang.seed_hist_v1 import (
    compute_seed_metrics_v1,
    load_slang_hist_v1,
    stable_packet_json,
    validate_seed_metrics_v1,
)


def test_slang_hist_seed_metrics_golden() -> None:
    packets = load_slang_hist_v1()
    mismatches = validate_seed_metrics_v1(packets)
    assert mismatches == []
    for pkt in packets:
        computed = compute_seed_metrics_v1(pkt)
        assert pkt.metrics is not None
        assert computed.model_dump() == pkt.metrics.model_dump()


def test_slang_hist_seed_metrics_bounds() -> None:
    packets = load_slang_hist_v1()
    for pkt in packets:
        metrics = compute_seed_metrics_v1(pkt)
        for key, value in metrics.model_dump().items():
            if key in {"status", "not_computable_reason", "method"}:
                continue
            assert isinstance(value, int)
            assert 0 <= value <= 100


def test_slang_hist_seed_missing_input() -> None:
    metrics = compute_seed_metrics_v1({"term": "missing_fields"})
    assert metrics.status == "not_computable"
    assert metrics.not_computable_reason is not None
    assert "missing" in metrics.not_computable_reason


def test_slang_hist_seed_stable_serialization() -> None:
    packets = load_slang_hist_v1()
    for pkt in packets:
        first = stable_packet_json(pkt)
        second = stable_packet_json(pkt)
        assert first == second
