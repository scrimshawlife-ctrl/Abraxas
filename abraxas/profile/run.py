"""Profile runner for deterministic benchmark suites."""

from __future__ import annotations

import json
import platform
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.policy.utp import load_active_utp
from abraxas.profile.jetson import detect_jetson, pin_clocks
from abraxas.profile.measure import measure_duration, process_rss_bytes
from abraxas.profile.schema import (
    BenchmarkDeterminism,
    BenchmarkMetrics,
    BenchmarkResult,
    DeviceInfo,
    ProfilePack,
    RunInfo,
)
from abraxas.profile.suite import benchmark_suite
from abraxas.runes.ctx import RuneInvocationContext


@dataclass(frozen=True)
class ProfileConfig:
    windows: int
    repetitions: int
    warmup_runs: int
    now_utc: str
    offline: bool
    cache_dir: str = "data/source_packets/2025"
    storage_index: str = "data/storage/index.jsonl"
    window_granularity: str = "weekly"
    pin_clocks: bool = False


def run_profile_suite(
    config: ProfileConfig, *, run_id: str, ctx: RuneInvocationContext
) -> Tuple[ProfilePack, Dict[str, List[str]]]:
    if config.pin_clocks:
        pin_clocks()

    jetson = detect_jetson()
    device = DeviceInfo(
        platform=jetson.platform or "unknown",
        os=platform.platform(),
        cpu=platform.processor() or "unknown",
        mem_total_bytes=_mem_total_bytes(),
    storage_free_bytes=_storage_free_bytes(Path(".")),
        gpu_present=jetson.gpu_present,
        clocks_pinned=jetson.clocks_pinned,
        power_mode=jetson.power_mode,
    )

    portfolio = load_active_utp()
    config_hashes = {
        "portfolio_ir_hash": portfolio.hash(),
        "lifecycle_hash": _load_lifecycle_hash(),
        "concurrency_config_hash": _concurrency_hash(portfolio),
    }

    run_info = RunInfo(
        run_id=run_id,
        now_utc=config.now_utc,
        repetitions=config.repetitions,
        warmup_runs=config.warmup_runs,
        config_hashes=config_hashes,
    )

    benchmarks: List[BenchmarkResult] = []
    state: Dict[str, Any] = {}
    hash_map: Dict[str, List[str]] = {}
    for definition in benchmark_suite():
        result, payload, hashes = _run_benchmark(definition, config, run_id, ctx, state)
        benchmarks.append(result)
        hash_map[definition.name] = hashes
        _apply_state(state, payload)

    return ProfilePack(device=device, run=run_info, benchmarks=benchmarks), hash_map


def _run_benchmark(
    definition,
    config: ProfileConfig,
    run_id: str,
    ctx: RuneInvocationContext,
    state: Dict[str, Any],
) -> Tuple[BenchmarkResult, Dict[str, Any], List[str]]:
    benchmark_ctx = {
        "windows": config.windows,
        "cache_dir": config.cache_dir,
        "storage_index": config.storage_index,
        "year": int(config.now_utc[:4]),
        "window_granularity": config.window_granularity,
        "window_start": None,
        "window_end": None,
        "now_utc": config.now_utc,
        "run_id": run_id,
        "ctx": ctx,
    }
    benchmark_ctx.update(state)

    warmup = max(0, config.warmup_runs)
    for _ in range(warmup):
        definition.runner(dict(benchmark_ctx))

    outputs: List[Dict[str, Any]] = []
    metrics_samples: List[BenchmarkMetrics] = []
    hashes: List[str] = []

    for _ in range(max(1, config.repetitions)):
        timer, payload = measure_duration(lambda: definition.runner(dict(benchmark_ctx)))
        payload = payload or {}
        output_hash = payload.get("output_hash") or sha256_hex(canonical_json(payload))
        hashes.append(output_hash)

        metrics_samples.append(
            BenchmarkMetrics(
                cpu_ms=timer.cpu_ms,
                latency_ms=timer.latency_ms,
                io_read_bytes=payload.get("io_read_bytes"),
                io_write_bytes=payload.get("io_write_bytes"),
                peak_rss_bytes=process_rss_bytes(),
                network_calls=0,
                network_bytes=0,
            )
        )
        outputs.append(payload)

    invariant = len(set(hashes)) == 1
    determinism = BenchmarkDeterminism(output_hash=hashes[0], invariant_across_reps=invariant)
    if not invariant:
        raise ValueError(f"Determinism violation for benchmark {definition.name}")

    metrics = _aggregate_metrics(metrics_samples)
    ubv_snapshot = {
        "cpu_ms": metrics.cpu_ms,
        "latency_ms": metrics.latency_ms,
        "io_read_bytes": metrics.io_read_bytes,
        "io_write_bytes": metrics.io_write_bytes,
        "peak_rss_bytes": metrics.peak_rss_bytes,
    }

    outputs_payload = outputs[0] if outputs else {}
    return (
        BenchmarkResult(
        name=definition.name,
        stage=definition.stage,
        inputs=outputs_payload.get("inputs") or {},
        outputs=outputs_payload.get("outputs") or {},
        metrics=metrics,
        ubv_snapshot=ubv_snapshot,
        determinism=determinism,
        provenance=outputs_payload.get("provenance") or {},
        ),
        outputs_payload,
        hashes,
    )


def _aggregate_metrics(samples: List[BenchmarkMetrics]) -> BenchmarkMetrics:
    def avg(values: List[int | None]) -> int | None:
        filtered = [v for v in values if v is not None]
        if not filtered:
            return None
        return int(round(sum(filtered) / len(filtered)))

    return BenchmarkMetrics(
        cpu_ms=avg([s.cpu_ms for s in samples]),
        latency_ms=avg([s.latency_ms for s in samples]),
        io_read_bytes=avg([s.io_read_bytes for s in samples]),
        io_write_bytes=avg([s.io_write_bytes for s in samples]),
        peak_rss_bytes=avg([s.peak_rss_bytes for s in samples]),
        network_calls=avg([s.network_calls for s in samples]),
        network_bytes=avg([s.network_bytes for s in samples]),
    )


def _apply_state(state: Dict[str, Any], payload: Dict[str, Any]) -> None:
    for key in ("packets", "frames", "influence", "synchronicity", "atlas"):
        if key in payload:
            state[key] = payload[key]


def _storage_free_bytes(path: Path) -> int:
    try:
        usage = shutil.disk_usage(path)
    except FileNotFoundError:
        return 0
    return int(usage.free)


def _mem_total_bytes() -> int:
    meminfo = Path("/proc/meminfo")
    if meminfo.exists():
        for line in meminfo.read_text(encoding="utf-8").splitlines():
            if line.startswith("MemTotal"):
                parts = line.split()
                if len(parts) >= 2:
                    return int(parts[1]) * 1024
    return 0


def _load_lifecycle_hash() -> str:
    pointer = Path(".aal/storage/LIFECYCLE_ACTIVE.json")
    if not pointer.exists():
        return "unknown"
    payload = pointer.read_text(encoding="utf-8")
    active_path = None
    try:
        active_path = json.loads(payload).get("active_path")
    except Exception:
        active_path = None
    if active_path:
        ir_path = pointer.parent / active_path
        if ir_path.exists():
            return sha256_hex(ir_path.read_text(encoding="utf-8"))
    return sha256_hex(payload)


def _concurrency_hash(portfolio) -> str:
    return sha256_hex(canonical_json({"pipeline": portfolio.pipeline.__dict__}))
