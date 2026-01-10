"""ABX-Rune Acquisition Layer - Bulk vs Surgical acquisition patterns.

Performance Drop v1.0 - Deterministic acquisition with budget enforcement.

Implements three acquisition runes:
- ABX-ACQUIRE_BULK (ß‚): Bulk acquisition via official APIs
- ABX-ACQUIRE_CACHE_ONLY (ß‚‚): Cache-only replay
- ABX-ACQUIRE_SURGICAL (ß‚ƒ): Surgical Decodo gate with caps

All runes are provenance-tracked and ERS-budget aware.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Literal

from abraxas.storage.cas import cas_put_bytes, cas_put_json, cas_exists
from abraxas.storage.hashes import stable_hash_json
from abraxas.perf.ledger import write_perf_event
from abraxas.perf.schema import PerfEvent


ReasonCode = Literal["BLOCKED", "MANIFEST_DISCOVERY", "JS_REQUIRED", "FALLBACK"]


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
    - Uses adapter.fetch with cache-first policy
    - Stores raw + parsed in CAS
    - Returns SourcePacket paths (not in-memory blobs)
    - Never calls Decodo (uses official bulk endpoints only)

    Args:
        source_id: Source identifier (e.g., "NOAA_NCEI_CDO_V2")
        window_utc: ISO8601 timestamp for window
        params: Adapter-specific parameters
        run_ctx: Run context with run_id, budget info
        strict_execution: If True, raises NotImplementedError for unimplemented

    Returns:
        Dict with keys: raw_path, parsed_path, cache_hit, provenance
    """
    if strict_execution:
        raise NotImplementedError(
            "ABX-ACQUIRE_BULK requires adapter integration. "
            "Implement adapter.fetch(source_id, window_utc, params) first."
        )

    # Stub implementation - returns placeholder paths
    run_id = run_ctx.get("run_id", "STUB_RUN")

    # Compute cache key
    cache_key = stable_hash_json({
        "source_id": source_id,
        "window_utc": window_utc,
        "params": params,
    })

    # Check cache
    cache_hit = cas_exists(cache_key)

    # Track performance
    start_time = time.time()

    if not cache_hit:
        # Simulate bulk fetch (stub - would call actual adapter)
        raw_data = b'{"stub": "bulk_fetch_data"}'
        parsed_data = {"stub": "parsed_data"}

        # Store in CAS
        raw_path = cas_put_bytes(
            "raw",
            raw_data,
            source_id,
            timestamp_utc=window_utc,
            meta={"run_id": run_id, "adapter": "stub"},
        )
        parsed_path = cas_put_json(
            "parsed",
            parsed_data,
            source_id,
            timestamp_utc=window_utc,
            meta={"run_id": run_id},
        )
    else:
        # Use cached paths (stub)
        raw_path = Path(f"/stub/raw/{cache_key}")
        parsed_path = Path(f"/stub/parsed/{cache_key}")

    duration_ms = (time.time() - start_time) * 1000

    # Write perf event
    perf_event = PerfEvent(
        run_id=run_id,
        op_name="acquire",
        source_id=source_id,
        bytes_in=0,
        bytes_out=len(b'{"stub": "bulk_fetch_data"}') if not cache_hit else 0,
        duration_ms=duration_ms,
        cache_hit=cache_hit,
        decodo_used=False,
        reason_code="bulk_api",
        provenance_hashes={"cache_key": cache_key},
    )
    write_perf_event(perf_event)

    return {
        "raw_path": str(raw_path),
        "parsed_path": str(parsed_path),
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
    """Apply ABX-ACQUIRE_CACHE_ONLY rune - cache-only replay.

    Behavior:
    - FAILS if cache missing (clear error)
    - NEVER touches network
    - Returns cached SourcePacket paths

    Args:
        cache_keys: List of cache keys to retrieve
        run_ctx: Run context
        strict_execution: If True, raises NotImplementedError

    Returns:
        Dict with keys: paths, cache_hits, failures
    """
    if strict_execution:
        raise NotImplementedError("ABX-ACQUIRE_CACHE_ONLY requires CAS integration")

    run_id = run_ctx.get("run_id", "STUB_RUN")
    start_time = time.time()

    paths = []
    failures = []

    for cache_key in cache_keys:
        if cas_exists(cache_key):
            paths.append(f"/stub/cache/{cache_key}")
        else:
            failures.append(cache_key)

    duration_ms = (time.time() - start_time) * 1000

    # Write perf event
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

    if failures:
        return {
            "paths": paths,
            "cache_hits": len(paths),
            "failures": failures,
            "error": f"Cache miss for {len(failures)} keys",
        }

    return {
        "paths": paths,
        "cache_hits": len(paths),
        "failures": [],
    }


def apply_acquire_surgical(
    target: str,
    reason_code: ReasonCode,
    hard_cap_requests: int,
    run_ctx: Dict[str, Any],
    *,
    strict_execution: bool = False,
) -> Dict[str, Any]:
    """Apply ABX-ACQUIRE_SURGICAL rune - surgical Decodo gate with caps.

    Behavior:
    - ENFORCES hard_cap_requests (absolute limit)
    - REQUIRES caching of every response in CAS
    - MUST support offline replay
    - MUST log decodo_used=True with reason_code
    - MUST NOT iterate discovered URLs automatically

    Args:
        target: URL or descriptor to scrape
        reason_code: Reason for surgical acquisition (BLOCKED, MANIFEST_DISCOVERY, JS_REQUIRED)
        hard_cap_requests: Absolute request cap (enforced)
        run_ctx: Run context with budget tracking
        strict_execution: If True, raises NotImplementedError

    Returns:
        Dict with keys: manifest_candidates, cached_paths, requests_used, provenance

    Raises:
        RuntimeError: If hard_cap_requests exceeded
    """
    if strict_execution:
        raise NotImplementedError(
            "ABX-ACQUIRE_SURGICAL requires Decodo adapter integration. "
            "Implement decodo.fetch_surgical(target, cap) first."
        )

    run_id = run_ctx.get("run_id", "STUB_RUN")
    start_time = time.time()

    # Stub implementation - simulates Decodo call with caching
    if hard_cap_requests <= 0:
        raise RuntimeError(f"Invalid hard_cap_requests: {hard_cap_requests}")

    # Simulate surgical fetch (would call Decodo in real implementation)
    # For now, return stub manifest candidates
    manifest_candidates = [
        {"url": f"{target}/manifest1", "type": "json"},
        {"url": f"{target}/manifest2", "type": "xml"},
    ]

    # Simulate caching of responses
    cached_paths = []
    for i, candidate in enumerate(manifest_candidates[:hard_cap_requests]):
        stub_response = f'{{"stub": "response_{i}"}}'
        cache_path = cas_put_bytes(
            "raw",
            stub_response.encode("utf-8"),
            "decodo_surgical",
            meta={
                "run_id": run_id,
                "target": target,
                "reason_code": reason_code,
                "request_index": i,
            },
        )
        cached_paths.append(str(cache_path))

    requests_used = min(len(manifest_candidates), hard_cap_requests)
    duration_ms = (time.time() - start_time) * 1000

    # Write perf event - MUST log decodo_used=True
    perf_event = PerfEvent(
        run_id=run_id,
        op_name="acquire",
        source_id="decodo_surgical",
        bytes_in=0,
        bytes_out=sum(len(f'{{"stub": "response_{i}"}}') for i in range(requests_used)),
        duration_ms=duration_ms,
        cache_hit=False,
        decodo_used=True,  # CRITICAL: Mark Decodo usage
        reason_code=reason_code,
        provenance_hashes={
            "target": stable_hash_json(target),
        },
    )
    write_perf_event(perf_event)

    # Enforce hard cap
    if len(manifest_candidates) > hard_cap_requests:
        return {
            "manifest_candidates": manifest_candidates[:hard_cap_requests],
            "cached_paths": cached_paths,
            "requests_used": requests_used,
            "requests_capped": True,
            "warning": f"Capped at {hard_cap_requests} requests (reason: {reason_code})",
            "provenance": {
                "run_id": run_id,
                "target": target,
                "reason_code": reason_code,
            },
        }

    return {
        "manifest_candidates": manifest_candidates,
        "cached_paths": cached_paths,
        "requests_used": requests_used,
        "requests_capped": False,
        "provenance": {
            "run_id": run_id,
            "target": target,
            "reason_code": reason_code,
        },
    }
