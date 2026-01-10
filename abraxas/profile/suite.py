"""Deterministic offline benchmark suite."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

from abraxas.atlas.construct import build_atlas_pack
from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.runes.invoke import invoke_capability
from abraxas.sonification.emit import emit_audio_controls
from abraxas.visuals.emit import emit_visual_controls
from abraxas.storage.lifecycle_ir import load_lifecycle_ir
from abraxas.storage.lifecycle_run import summarize_storage
from abraxas.storage.index import StorageIndex


@dataclass(frozen=True)
class BenchmarkDefinition:
    name: str
    stage: str
    runner: Any


def benchmark_suite() -> List[BenchmarkDefinition]:
    return [
        BenchmarkDefinition("PACKET_LOAD_OFFLINE", "PACKETIZE", _benchmark_packet_load),
        BenchmarkDefinition("TVM_FRAME_BUILD", "ANALYZE", _benchmark_tvm_frames),
        BenchmarkDefinition("INFLUENCE_SYNCH", "ANALYZE", _benchmark_influence_synch),
        BenchmarkDefinition("ATLAS_BUILD", "ATLAS", _benchmark_atlas_build),
        BenchmarkDefinition("SONIFY_CONTROLS", "SONIFY", _benchmark_sonify),
        BenchmarkDefinition("VISUAL_CONTROLS", "VISUALIZE", _benchmark_visualize),
        BenchmarkDefinition("OBSERVE_SUMMARIES", "OBSERVE", _benchmark_observe),
    ]


def _benchmark_packet_load(ctx: Dict[str, Any]) -> Dict[str, Any]:
    cache_dir = Path(ctx.get("cache_dir") or "data/source_packets/2025")
    windows = int(ctx.get("windows") or 1)
    packet_files = sorted(cache_dir.glob("*.json"))
    if not packet_files:
        return {"not_computable": True, "reason": "cache_missing"}
    selected = packet_files[: max(1, windows)]
    packets = []
    bytes_read = 0
    for path in selected:
        data = path.read_bytes()
        bytes_read += len(data)
        packets.append(json.loads(data))
    output_hash = sha256_hex(canonical_json(packets))
    return {
        "packets": packets,
        "output_hash": output_hash,
        "io_read_bytes": bytes_read,
        "inputs": {"files": [str(p) for p in selected]},
        "outputs": {"packet_count": len(packets)},
    }


def _benchmark_tvm_frames(ctx: Dict[str, Any]) -> Dict[str, Any]:
    packet_payload = ctx.get("packets")
    if not packet_payload:
        return {"not_computable": True, "reason": "packets_missing"}
    metrics = invoke_capability("rune:metric_extract", {"packets": packet_payload}, ctx=ctx["ctx"])
    frames = invoke_capability(
        "rune:tvm_frame",
        {
            "metrics": metrics.get("metrics") or [],
            "window_start_utc": ctx.get("window_start"),
            "window_end_utc": ctx.get("window_end"),
        },
        ctx=ctx["ctx"],
    )
    frame_list = frames.get("frames") or []
    output_hash = sha256_hex(canonical_json(frame_list))
    return {
        "frames": frame_list,
        "output_hash": output_hash,
        "inputs": {"packet_count": len(packet_payload)},
        "outputs": {"frame_count": len(frame_list)},
    }


def _benchmark_influence_synch(ctx: Dict[str, Any]) -> Dict[str, Any]:
    frames = ctx.get("frames")
    if not frames:
        return {"not_computable": True, "reason": "frames_missing"}
    flat_frames = [_flatten_frame(frame) for frame in frames]
    influence = invoke_capability("rune:influence_detect", {"frames": flat_frames}, ctx=ctx["ctx"])
    synch = invoke_capability("rune:synchronicity_map", {"frames": flat_frames}, ctx=ctx["ctx"])
    payload = {"influence": influence, "synch": synch}
    output_hash = sha256_hex(canonical_json(payload))
    return {
        "influence": influence,
        "synchronicity": synch,
        "output_hash": output_hash,
        "outputs": {"influence_keys": len(influence), "synch_keys": len(synch)},
    }


def _benchmark_atlas_build(ctx: Dict[str, Any]) -> Dict[str, Any]:
    frames = ctx.get("frames")
    influence = ctx.get("influence")
    synch = ctx.get("synchronicity")
    if not frames or influence is None or synch is None:
        return {"not_computable": True, "reason": "inputs_missing"}
    seedpack = {
        "year": int(ctx.get("year") or 0),
        "frames": frames,
        "influence": influence,
        "synchronicity": synch,
        "provenance": {"run_id": ctx.get("run_id", "profile")},
    }
    atlas_pack = build_atlas_pack(seedpack, window_granularity=ctx.get("window_granularity", "weekly"))
    output_hash = atlas_pack.atlas_hash()
    return {
        "atlas": atlas_pack.model_dump(),
        "output_hash": output_hash,
        "outputs": {"frames_count": atlas_pack.frames_count},
    }


def _benchmark_sonify(ctx: Dict[str, Any]) -> Dict[str, Any]:
    atlas = ctx.get("atlas")
    if not atlas:
        return {"not_computable": True, "reason": "atlas_missing"}
    frames = emit_audio_controls(atlas)
    payload = [frame.model_dump() for frame in frames]
    output_hash = sha256_hex(canonical_json(payload))
    return {
        "audio_frames": payload,
        "output_hash": output_hash,
        "outputs": {"frame_count": len(payload)},
    }


def _benchmark_visualize(ctx: Dict[str, Any]) -> Dict[str, Any]:
    atlas = ctx.get("atlas")
    if not atlas:
        return {"not_computable": True, "reason": "atlas_missing"}
    frames = emit_visual_controls(atlas)
    payload = [frame.model_dump() for frame in frames]
    output_hash = sha256_hex(canonical_json(payload))
    return {
        "visual_frames": payload,
        "output_hash": output_hash,
        "outputs": {"frame_count": len(payload)},
    }


def _benchmark_observe(ctx: Dict[str, Any]) -> Dict[str, Any]:
    index_path = Path(ctx.get("storage_index") or "data/storage/index.jsonl")
    if not index_path.exists():
        return {"not_computable": True, "reason": "index_missing"}
    index = StorageIndex.from_jsonl(index_path)
    lifecycle_ir = load_lifecycle_ir(ctx.get("now_utc", "1970-01-01T00:00:00Z"))
    summary = summarize_storage(index, ctx.get("now_utc", "1970-01-01T00:00:00Z"), lifecycle_ir)
    output_hash = sha256_hex(canonical_json(summary))
    return {
        "summary": summary,
        "output_hash": output_hash,
        "inputs": {"index_path": str(index_path)},
    }


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
