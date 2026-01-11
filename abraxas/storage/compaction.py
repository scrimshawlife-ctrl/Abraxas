"""Compaction engine for parsed/packets/ledger artifacts."""

from __future__ import annotations

import json
import time
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.storage.index import StorageIndex, StorageIndexEntry
from abraxas.storage.lifecycle_schema import LifecycleIR


@dataclass(frozen=True)
class CompactionStep:
    action: str
    path: str
    artifact_type: str
    source_id: str
    created_at_utc: str
    tier: str
    reason: str
    bytes_expected: int
    target_codec: str


@dataclass(frozen=True)
class CompactionPlan:
    steps: List[CompactionStep]


def plan_compaction(index: StorageIndex, lifecycle_ir: LifecycleIR, now_utc: str) -> CompactionPlan:
    steps: List[CompactionStep] = []
    for entry in index.sorted_entries():
        policy = lifecycle_ir.artifacts.get(entry.artifact_type)
        if not policy or not policy.retain:
            continue
        if entry.artifact_type not in {"parsed", "packets", "ledger"}:
            continue
        target_codec = _codec_for_tier(entry.tier, lifecycle_ir)
        if entry.codec == target_codec:
            continue
        steps.append(
            CompactionStep(
                action="COMPACT",
                path=entry.path,
                artifact_type=entry.artifact_type,
                source_id=entry.source_id,
                created_at_utc=entry.created_at_utc,
                tier=entry.tier,
                reason=f"codec:{entry.codec}-> {target_codec}",
                bytes_expected=entry.size_bytes,
                target_codec=target_codec,
            )
        )
    return CompactionPlan(steps=steps)


def execute_compaction(
    plan: CompactionPlan,
    lifecycle_ir: LifecycleIR,
    *,
    max_files: int,
    max_cpu_ms: int,
    max_bytes_written: int,
) -> Tuple[StorageIndex, List[Dict[str, Any]]]:
    events: List[Dict[str, Any]] = []
    index_updates: List[StorageIndexEntry] = []
    start = time.monotonic()
    bytes_written = 0
    files_written = 0

    for step in plan.steps:
        if files_written >= max_files:
            break
        elapsed_ms = int((time.monotonic() - start) * 1000)
        if elapsed_ms >= max_cpu_ms:
            break
        source_path = Path(step.path)
        if not source_path.exists():
            continue
        original_bytes = source_path.read_bytes()
        canonical = _canonicalize_bytes(original_bytes)
        canonical_hash = sha256_hex(canonical)
        compressed = _compress(canonical, step.target_codec, lifecycle_ir)
        if len(compressed) >= len(original_bytes):
            continue

        target_path = source_path.with_suffix(source_path.suffix + ".zst")
        if bytes_written + len(compressed) > max_bytes_written:
            break
        target_path.write_bytes(compressed)
        bytes_written += len(compressed)
        files_written += 1

        index_updates.append(
            StorageIndexEntry(
                artifact_type=step.artifact_type,
                source_id=step.source_id,
                created_at_utc=step.created_at_utc,
                size_bytes=len(compressed),
                codec=step.target_codec,
                tier=step.tier,
                path=str(target_path),
                content_hash=sha256_hex(compressed),
                superseded_by=None,
            )
        )
        events.append(
            {
                "event": "compact",
                "path": str(source_path),
                "new_path": str(target_path),
                "bytes_before": len(original_bytes),
                "bytes_after": len(compressed),
                "canonical_hash": canonical_hash,
            }
        )

    return StorageIndex(index_updates), events


def _canonicalize_bytes(data: bytes) -> bytes:
    try:
        payload = json.loads(data)
    except Exception:
        return _canonicalize_jsonl(data)
    return canonical_json(payload).encode("utf-8")


def _canonicalize_jsonl(data: bytes) -> bytes:
    text = data.decode("utf-8", errors="ignore")
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return data
    try:
        payload = [json.loads(line) for line in lines]
    except Exception:
        return data
    return canonical_json(payload).encode("utf-8")


def _compress(data: bytes, codec: str, lifecycle_ir: LifecycleIR) -> bytes:
    level = _zstd_level_for(codec, lifecycle_ir)
    return zlib.compress(data, level)


def _codec_for_tier(tier: str, lifecycle_ir: LifecycleIR) -> str:
    tier_policy = lifecycle_ir.tiers.get(tier)
    return tier_policy.codec if tier_policy else "zstd"


def _zstd_level_for(codec: str, lifecycle_ir: LifecycleIR) -> int:
    if codec == "lz4":
        return 1
    if codec == "zstd":
        cold = lifecycle_ir.tiers.get("cold")
        return cold.zstd_level if cold else 3
    return 3
