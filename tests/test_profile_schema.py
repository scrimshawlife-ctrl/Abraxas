from __future__ import annotations

from abraxas.profile.schema import BenchmarkDeterminism, BenchmarkMetrics, BenchmarkResult, DeviceInfo, ProfilePack, RunInfo


def test_profile_pack_hash_stable() -> None:
    device = DeviceInfo(
        platform="unknown",
        os="test",
        cpu="cpu",
        mem_total_bytes=1,
        storage_free_bytes=2,
        gpu_present=False,
        clocks_pinned=False,
        power_mode=None,
    )
    run = RunInfo(run_id="run", now_utc="2026-01-01T00:00:00Z", repetitions=1, warmup_runs=0)
    bench = BenchmarkResult(
        name="PACKET_LOAD_OFFLINE",
        stage="PACKETIZE",
        inputs={},
        outputs={},
        metrics=BenchmarkMetrics(cpu_ms=1, latency_ms=2),
        ubv_snapshot={},
        determinism=BenchmarkDeterminism(output_hash="hash", invariant_across_reps=True),
        provenance={},
    )
    pack = ProfilePack(device=device, run=run, benchmarks=[bench])
    assert pack.profile_hash() == pack.profile_hash()
