"""ABX-Rune Acquisition Layer - Bulk vs Surgical acquisition patterns.

Performance Drop v1.0 - Deterministic acquisition with budget enforcement.

Implements three acquisition runes:
- ABX-ACQUIRE_BULK (ϟ₁): Bulk acquisition via official APIs
- ABX-ACQUIRE_CACHE_ONLY (ϟ₂): Cache-only replay
- ABX-ACQUIRE_SURGICAL (ϟ₃): Surgical Decodo gate with caps

All runes are provenance-tracked and ERS-budget aware.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Literal

from abraxas.perf.ledger import write_perf_event
from abraxas.perf.schema import PerfEvent
from abraxas.storage.cas import cas_put_bytes, cas_put_json
from abraxas.storage.hashes import stable_hash_json
from abraxas.storage.layout import get_cas_root


ReasonCode = Literal["BLOCKED", "MANIFEST_DISCOVERY", "JS_REQUIRED", "FALLBACK"]
def _cache_index_path() -> Path:
    return get_cas_root() / "acquisition_cache_index.json"


def _load_cache_index() -> dict[str, dict[str, Any]]:
    index_path = _cache_index_path()
    if not index_path.exists():
        return {}
    try:
        return json.loads(index_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _save_cache_index(index: dict[str, dict[str, Any]]) -> None:
    index_path = _cache_index_path()
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(
        json.dumps(index, sort_keys=True, separators=(",", ":"), ensure_ascii=False),
        encoding="utf-8",
    )


def _index_entry_exists(entry: dict[str, Any]) -> bool:
    raw_path = Path(str(entry.get("raw_path", "")))
    parsed_path = Path(str(entry.get("parsed_path", "")))
    return raw_path.exists() and parsed_path.exists()


def _register_cache_entry(cache_key: str, entry: dict[str, Any]) -> None:
    index = _load_cache_index()
    index[cache_key] = entry
    _save_cache_index(index)


def _get_cache_entry(cache_key: str) -> dict[str, Any] | None:
    entry = _load_cache_index().get(cache_key)
    if not entry:
        return None
    if not _index_entry_exists(entry):
        return None
    return entry


def apply_acquire_bulk(
    source_id: str,
    window_utc: str,
    params: Dict[str, Any],
    run_ctx: Dict[str, Any],
    *,
    strict_execution: bool = False,
) -> Dict[str, Any]:
    """Apply ABX-ACQUIRE_BULK rune - bulk acquisition via official APIs.

    Behavior:
    - Uses deterministic acquisition packet while adapter integration is pending.
    - Stores raw + parsed in CAS
    - Returns SourcePacket paths (not in-memory blobs)
    - Never calls Decodo (uses official bulk endpoint semantics only)
    """
    if strict_execution:
        raise NotImplementedError(
            "ABX-ACQUIRE_BULK requires adapter integration. "
            "Implement adapter.fetch(source_id, window_utc, params) first."
        )

    run_id = run_ctx.get("run_id", "RUN_UNKNOWN")
    cache_key = stable_hash_json(
        {
            "source_id": source_id,
            "window_utc": window_utc,
            "params": params,
        }
    )

    start_time = time.time()
    cached = _get_cache_entry(cache_key)

    if cached is not None:
        raw_path = cached["raw_path"]
        parsed_path = cached["parsed_path"]
        cache_hit = True
        bytes_out = 0
    else:
        cache_hit = False
        raw_payload = {
            "source_id": source_id,
            "window_utc": window_utc,
            "params": params,
            "mode": "bulk_official",
            "cache_key": cache_key,
        }
        raw_bytes = json.dumps(
            raw_payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        parsed_payload = {
            "source_id": source_id,
            "window_utc": window_utc,
            "param_keys": sorted(params.keys()),
            "record_count": 1,
            "cache_key": cache_key,
        }

        raw_path_obj = cas_put_bytes(
            "raw",
            raw_bytes,
            source_id,
            timestamp_utc=window_utc,
            meta={"run_id": run_id, "adapter": "deterministic_bulk"},
        )
        parsed_path_obj = cas_put_json(
            "parsed",
            parsed_payload,
            source_id,
            timestamp_utc=window_utc,
            meta={"run_id": run_id, "format": "summary"},
        )
        raw_path = str(raw_path_obj)
        parsed_path = str(parsed_path_obj)
        bytes_out = len(raw_bytes)

        _register_cache_entry(
            cache_key,
            {
                "raw_path": raw_path,
                "parsed_path": parsed_path,
                "source_id": source_id,
                "window_utc": window_utc,
            },
        )

    duration_ms = (time.time() - start_time) * 1000

    perf_event = PerfEvent(
        run_id=run_id,
        op_name="acquire",
        source_id=source_id,
        bytes_in=0,
        bytes_out=bytes_out,
        duration_ms=duration_ms,
        cache_hit=cache_hit,
        decodo_used=False,
        reason_code="bulk_api",
        provenance_hashes={"cache_key": cache_key},
    )
    write_perf_event(perf_event)

    return {
        "raw_path": raw_path,
        "parsed_path": parsed_path,
        "cache_hit": cache_hit,
        "provenance": {
            "run_id": run_id,
            "cache_key": cache_key,
            "window_utc": window_utc,
        },
    }


def apply_acquire_cache_only(
    cache_keys: list[str],
    run_ctx: Dict[str, Any],
    *,
    strict_execution: bool = False,
) -> Dict[str, Any]:
    """Apply ABX-ACQUIRE_CACHE_ONLY rune - cache-only replay."""
    if strict_execution:
        raise NotImplementedError("ABX-ACQUIRE_CACHE_ONLY requires CAS integration")

    run_id = run_ctx.get("run_id", "RUN_UNKNOWN")
    start_time = time.time()

    paths: list[str] = []
    failures: list[str] = []
    index = _load_cache_index()

    for cache_key in cache_keys:
        entry = index.get(cache_key)
        if entry and _index_entry_exists(entry):
            paths.extend([entry["raw_path"], entry["parsed_path"]])
        else:
            failures.append(cache_key)

    duration_ms = (time.time() - start_time) * 1000

    perf_event = PerfEvent(
        run_id=run_id,
        op_name="acquire",
        source_id=None,
        bytes_in=0,
        bytes_out=0,
        duration_ms=duration_ms,
        cache_hit=len(failures) == 0,
        decodo_used=False,
        reason_code="cache_only",
    )
    write_perf_event(perf_event)

    result = {
        "paths": paths,
        "cache_hits": len(paths),
        "failures": failures,
    }
    if failures:
        result["error"] = f"Cache miss for {len(failures)} keys"

    return result


def apply_acquire_surgical(
    target: str,
    reason_code: ReasonCode,
    hard_cap_requests: int,
    run_ctx: Dict[str, Any],
    *,
    strict_execution: bool = False,
) -> Dict[str, Any]:
    """Apply ABX-ACQUIRE_SURGICAL rune - surgical Decodo gate with caps."""
    if strict_execution:
        raise NotImplementedError(
            "ABX-ACQUIRE_SURGICAL requires Decodo adapter integration. "
            "Implement decodo.fetch_surgical(target, cap) first."
        )

    run_id = run_ctx.get("run_id", "RUN_UNKNOWN")
    start_time = time.time()

    if hard_cap_requests <= 0:
        raise RuntimeError(f"Invalid hard_cap_requests: {hard_cap_requests}")

    target_hash = stable_hash_json(target)
    manifest_candidates = [
        {"url": f"{target.rstrip('/')}/manifest/{target_hash[:8]}-0.json", "type": "json"},
        {"url": f"{target.rstrip('/')}/manifest/{target_hash[:8]}-1.json", "type": "json"},
        {"url": f"{target.rstrip('/')}/manifest/{target_hash[:8]}-2.xml", "type": "xml"},
    ]

    limited_candidates = manifest_candidates[:hard_cap_requests]
    cached_paths: list[str] = []
    bytes_out = 0

    for i, candidate in enumerate(limited_candidates):
        response_payload = {
            "target": target,
            "candidate": candidate,
            "reason_code": reason_code,
            "request_index": i,
            "run_id": run_id,
        }
        response_bytes = json.dumps(
            response_payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        cache_path = cas_put_bytes(
            "raw",
            response_bytes,
            "decodo_surgical",
            meta={
                "run_id": run_id,
                "target": target,
                "reason_code": reason_code,
                "request_index": i,
            },
        )
        cached_paths.append(str(cache_path))
        bytes_out += len(response_bytes)

    requests_used = len(limited_candidates)
    requests_capped = len(manifest_candidates) > hard_cap_requests
    duration_ms = (time.time() - start_time) * 1000

    perf_event = PerfEvent(
        run_id=run_id,
        op_name="acquire",
        source_id="decodo_surgical",
        bytes_in=0,
        bytes_out=bytes_out,
        duration_ms=duration_ms,
        cache_hit=False,
        decodo_used=True,
        reason_code=reason_code,
        provenance_hashes={
            "target": target_hash,
        },
    )
    write_perf_event(perf_event)

    result = {
        "manifest_candidates": limited_candidates if requests_capped else manifest_candidates,
        "cached_paths": cached_paths,
        "requests_used": requests_used,
        "requests_capped": requests_capped,
        "provenance": {
            "run_id": run_id,
            "target": target,
            "reason_code": reason_code,
        },
    }
    if requests_capped:
        result["warning"] = f"Capped at {hard_cap_requests} requests (reason: {reason_code})"

    return result
