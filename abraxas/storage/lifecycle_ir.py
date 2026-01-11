"""Lifecycle IR loader with atomic pointer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from abraxas.policy.utp import PortfolioTuningIR, load_active_utp
from abraxas.storage.lifecycle_schema import (
    ArtifactPolicy,
    CompactionPolicy,
    EvictionPolicy,
    LifecycleIR,
    LifecycleProvenance,
    TierPolicy,
)


DEFAULT_POINTER_PATH = Path(".aal/storage/LIFECYCLE_ACTIVE.json")


def default_lifecycle_ir(now_utc: str, portfolio: PortfolioTuningIR) -> LifecycleIR:
    tiers = {
        "hot": TierPolicy(max_age_days=7, codec="lz4", zstd_level=3, dict_enabled=False),
        "cold": TierPolicy(min_age_days=7, codec="zstd", zstd_level=6, dict_enabled=True),
        "deep_archive": TierPolicy(min_age_days=30, codec="zstd", zstd_level=9, dict_enabled=True),
    }
    artifacts = {
        "raw": ArtifactPolicy(retain=True, allow_relocate=True, allow_delete=False),
        "parsed": ArtifactPolicy(retain=True, allow_delete=True, delete_after_days=30, rebuildable=True),
        "packets": ArtifactPolicy(retain=True, allow_delete=True, delete_after_days=30, rebuildable=True),
        "ledger": ArtifactPolicy(retain=True, allow_delete=False, rebuildable=False),
        "dict": ArtifactPolicy(retain=True, allow_delete=False, rebuildable=True),
    }
    provenance = LifecycleProvenance(
        derived_from_portfolio_ir_hash=portfolio.hash(),
        created_at_utc=now_utc,
        author="system",
    )
    return LifecycleIR(
        tiers=tiers,
        artifacts=artifacts,
        compaction=CompactionPolicy(),
        eviction=EvictionPolicy(),
        provenance=provenance,
    )


def load_lifecycle_ir(now_utc: str, pointer_path: Optional[Path] = None) -> LifecycleIR:
    pointer_path = pointer_path or DEFAULT_POINTER_PATH
    if pointer_path.exists():
        payload = json.loads(pointer_path.read_text(encoding="utf-8"))
        active_path = payload.get("active_path")
        if active_path:
            ir_path = (pointer_path.parent / active_path).resolve()
            if ir_path.exists():
                ir_payload = json.loads(ir_path.read_text(encoding="utf-8"))
                return LifecycleIR(**ir_payload)
    portfolio = load_active_utp()
    return default_lifecycle_ir(now_utc, portfolio)


def write_lifecycle_ir(ir: LifecycleIR, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ir.model_dump(), indent=2, sort_keys=True), encoding="utf-8")


def write_pointer(active_path: Path, pointer_path: Optional[Path] = None) -> None:
    pointer_path = pointer_path or DEFAULT_POINTER_PATH
    pointer_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = pointer_path.with_suffix(".tmp")
    payload = {"active_path": str(active_path.name)}
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp_path.replace(pointer_path)
