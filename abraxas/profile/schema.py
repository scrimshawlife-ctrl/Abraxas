"""ProfilePack schema for deterministic hardware profiling."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex


class DeviceInfo(BaseModel):
    platform: str
    os: str
    cpu: str
    mem_total_bytes: int
    storage_free_bytes: int
    gpu_present: bool
    clocks_pinned: bool
    power_mode: Optional[str] = None


class RunInfo(BaseModel):
    run_id: str
    now_utc: str
    repetitions: int
    warmup_runs: int
    config_hashes: Dict[str, str] = Field(default_factory=dict)


class BenchmarkMetrics(BaseModel):
    cpu_ms: int | None = None
    latency_ms: int | None = None
    io_read_bytes: int | None = None
    io_write_bytes: int | None = None
    peak_rss_bytes: int | None = None
    network_calls: int | None = None
    network_bytes: int | None = None


class BenchmarkDeterminism(BaseModel):
    output_hash: str
    invariant_across_reps: bool


class BenchmarkResult(BaseModel):
    name: str
    stage: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    metrics: BenchmarkMetrics
    ubv_snapshot: Dict[str, Any] = Field(default_factory=dict)
    determinism: BenchmarkDeterminism
    provenance: Dict[str, Any] = Field(default_factory=dict)


class ProfilePack(BaseModel):
    profile_version: str = "1.0"
    device: DeviceInfo
    run: RunInfo
    benchmarks: List[BenchmarkResult]

    def canonical_payload(self) -> Dict[str, Any]:
        payload = self.model_dump()
        payload["benchmarks"] = [bench.model_dump() for bench in self.benchmarks]
        return payload

    def profile_hash(self) -> str:
        return sha256_hex(canonical_json(self.canonical_payload()))
