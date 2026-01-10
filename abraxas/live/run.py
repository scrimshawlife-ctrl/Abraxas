"""Live atlas runner for rolling windows."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from abraxas.atlas.construct import build_atlas_pack
from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.live.schema import LIVE_SCHEMA_VERSION, LiveAtlasPack
from abraxas.live.windowing import LiveWindowConfig, compute_live_windows, stable_now_utc
from abraxas.runes.ctx import RuneInvocationContext
from abraxas.runes.invoke import invoke_capability


@dataclass(frozen=True)
class LiveRunContext:
    run_id: str
    now_utc: str
    git_hash: str = "unknown"


def run_live_atlas(
    sources: Optional[List[str]],
    window_config: LiveWindowConfig,
    run_ctx: LiveRunContext,
    cache_dir: Path,
    *,
    live_version: str = LIVE_SCHEMA_VERSION,
) -> LiveAtlasPack:
    _ = sources
    now_utc = stable_now_utc(run_ctx)
    windows = compute_live_windows(now_utc, window_config)
    packets = _load_packets(cache_dir)
    window_packs = [
        _build_window_pack(window, packets, run_ctx, window_config.window_size)
        for window in windows
    ]
    source_cache_hashes = _hash_cache_files(cache_dir)

    live_pack = LiveAtlasPack(
        live_version=live_version,
        generated_at_utc=now_utc,
        window_config={
            "window_size": window_config.window_size,
            "step_size": window_config.step_size,
            "alignment": window_config.alignment,
            "retention": window_config.retention,
        },
        windows=window_packs,
        provenance={
            "source_cache_hashes": source_cache_hashes,
            "run_id": run_ctx.run_id,
            "live_hash": "",
        },
    )
    live_pack.provenance["live_hash"] = live_pack.live_hash()
    return live_pack


def _build_window_pack(
    window,
    packets: List[Dict[str, Any]],
    run_ctx: LiveRunContext,
    window_granularity: str,
) -> Dict[str, Any]:
    window_packets = [
        packet for packet in packets
        if (packet.get("window_start_utc") or "") <= window.end_utc and (packet.get("window_end_utc") or "") >= window.start_utc
    ]
    ctx = RuneInvocationContext(run_id=run_ctx.run_id, subsystem_id="live", git_hash=run_ctx.git_hash)
    metrics = invoke_capability("rune:metric_extract", {"packets": window_packets}, ctx=ctx)
    tvm_frame = invoke_capability(
        "rune:tvm_frame",
        {
            "metrics": metrics.get("metrics") or [],
            "window_start_utc": window.start_utc,
            "window_end_utc": window.end_utc,
        },
        ctx=ctx,
    )
    frames = tvm_frame.get("frames") or []
    influence_frames = [_flatten_frame(frame) for frame in frames]
    influence = invoke_capability("rune:influence_detect", {"frames": influence_frames}, ctx=ctx)
    synchronicity = invoke_capability("rune:synchronicity_map", {"frames": influence_frames}, ctx=ctx)

    seedpack = {
        "schema_version": "seedpack.v0.2",
        "year": _extract_year(window.start_utc),
        "frames": frames,
        "influence": influence,
        "synchronicity": synchronicity,
    }
    seedpack["seedpack_hash"] = sha256_hex(canonical_json(seedpack))
    atlas_pack = build_atlas_pack(seedpack, window_granularity=window_granularity)
    return atlas_pack.model_dump()


def _load_packets(cache_dir: Path) -> List[Dict[str, Any]]:
    packets: List[Dict[str, Any]] = []
    if not cache_dir.exists():
        return packets
    for path in sorted(cache_dir.glob("*.json")):
        packets.append(json.loads(path.read_text(encoding="utf-8")))
    return packets


def _flatten_frame(frame: Dict[str, Any]) -> Dict[str, Any]:
    vectors = frame.get("vectors") or {}
    flattened = {}
    for key, value in vectors.items():
        if isinstance(value, dict):
            flattened[key] = value.get("score")
        else:
            flattened[key] = value
    return {
        "window_start_utc": frame.get("window_start_utc"),
        "window_end_utc": frame.get("window_end_utc"),
        "domain": frame.get("domain") or "unknown",
        "data_grade": frame.get("data_grade") or "real",
        "vectors": flattened,
        "provenance": frame.get("provenance") or {},
    }


def _hash_cache_files(cache_dir: Path) -> List[Dict[str, str]]:
    entries: List[Dict[str, str]] = []
    if not cache_dir.exists():
        return entries
    for path in sorted(cache_dir.glob("*.json")):
        entries.append({"path": str(path.name), "hash": sha256_hex(path.read_text(encoding="utf-8"))})
    return entries


def _extract_year(iso_ts: str) -> int:
    return int(iso_ts[:4]) if iso_ts else 0
