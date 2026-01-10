"""ABX-MANIFEST_DISCOVER rune operator."""

from __future__ import annotations

from typing import Any, Dict, List

from abraxas.acquisition.manifest_discovery import discover_manifest
from abraxas.policy.utp import load_active_utp
from abraxas.storage.cas import CASStore


def apply_manifest_discover(
    *,
    source_id: str,
    seeds: List[str] | None = None,
    window: Dict[str, Any] | None = None,
    run_ctx: Dict[str, Any],
    strict_execution: bool = True,
) -> Dict[str, Any]:
    budgets = load_active_utp()
    cas_store = CASStore()
    result = discover_manifest(
        source_id=source_id,
        seed_targets=seeds or [],
        run_ctx=run_ctx,
        budgets=budgets,
        cas_store=cas_store,
        allow_decodo=True,
    )
    return {
        "manifest_artifact": result.manifest.model_dump(),
        "raw_ref": result.raw_ref,
        "parsed_ref": result.parsed_ref,
    }
