from __future__ import annotations

import pytest

from abraxas.profile.suite import benchmark_suite
from abraxas.runes.operators.offline_enforce import apply_offline_enforce
from abraxas.runes.operators.invariance_check import apply_invariance_check
from abraxas.profile.run import _aggregate_metrics
from abraxas.profile.schema import BenchmarkMetrics


def test_suite_ordering_stable() -> None:
    names = [bench.name for bench in benchmark_suite()]
    assert names == [
        "PACKET_LOAD_OFFLINE",
        "TVM_FRAME_BUILD",
        "INFLUENCE_SYNCH",
        "ATLAS_BUILD",
        "SONIFY_CONTROLS",
        "VISUAL_CONTROLS",
        "OBSERVE_SUMMARIES",
    ]


def test_offline_enforce_blocks() -> None:
    with pytest.raises(ValueError):
        apply_offline_enforce(offline=False)


def test_invariance_check_detects() -> None:
    with pytest.raises(ValueError):
        apply_invariance_check(hashes=["a", "b"])


def test_metric_aggregation_rounds() -> None:
    metrics = [
        BenchmarkMetrics(cpu_ms=10, latency_ms=20),
        BenchmarkMetrics(cpu_ms=11, latency_ms=21),
    ]
    aggregated = _aggregate_metrics(metrics)
    assert aggregated.cpu_ms == 10
    assert aggregated.latency_ms == 20
