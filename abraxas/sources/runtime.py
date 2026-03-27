"""Runtime helpers for executing SourceAtlas adapters."""

from __future__ import annotations

from pathlib import Path
import time
from typing import Any, Dict, Optional, Type

from abraxas.sources.adapters import (
    CLDRSnapshotAdapter,
    GovDocsJSONLAdapter,
    HTTPSnapshotAdapter,
    JPLHorizonsAdapter,
    LinguisticJSONLAdapter,
    NCEICDOAdapter,
    NISTBulletinsAdapter,
    SWPCKpAdapter,
    TimeSeriesCSVAdapter,
    TomskSOSAdapter,
    TZDBSnapshotAdapter,
)
from abraxas.sources.adapters.base import SourceAdapter
from abraxas.sources.atlas import get_source
from abraxas.sources.packets import SourcePacket
from abraxas.sources.types import SourceWindow


ADAPTER_REGISTRY: dict[str, Type[SourceAdapter]] = {
    "timeseries_csv": TimeSeriesCSVAdapter,
    "govdocs_jsonl": GovDocsJSONLAdapter,
    "linguistic_jsonl": LinguisticJSONLAdapter,
    "tzdb_snapshot": TZDBSnapshotAdapter,
    "ncei_cdo_v2": NCEICDOAdapter,
    "swpc_kp_json": SWPCKpAdapter,
    "jpl_horizons_api": JPLHorizonsAdapter,
    "cldr_snapshot": CLDRSnapshotAdapter,
    "nist_bulletin_pdf_index": NISTBulletinsAdapter,
    "tomsk_sos_scrape_cache": TomskSOSAdapter,
}


def resolve_adapter(adapter_name: str) -> SourceAdapter:
    cls = ADAPTER_REGISTRY.get(adapter_name)
    if cls is None:
        available = ", ".join(sorted(ADAPTER_REGISTRY.keys()))
        raise ValueError(f"Unknown source adapter: {adapter_name}. Available: {available}")
    return cls()


def run_source_once(
    *,
    source_id: str,
    window: SourceWindow,
    params: Dict[str, Any],
    cache_dir: Optional[Path],
    run_ctx: Optional[Dict[str, Any]] = None,
) -> list[SourcePacket]:
    source_spec = get_source(source_id)
    if source_spec is None:
        raise ValueError(f"Unknown SourceAtlas source_id: {source_id}")

    adapter = resolve_adapter(source_spec.adapter)
    return adapter.fetch_parse_emit(
        source_spec=source_spec,
        window=window,
        params=params,
        cache_dir=cache_dir,
        run_ctx=run_ctx or {},
    )


def run_sources_batch(
    *,
    source_ids: list[str],
    window: SourceWindow,
    params_by_source: Optional[dict[str, Dict[str, Any]]] = None,
    default_params: Optional[Dict[str, Any]] = None,
    cache_dir: Optional[Path] = None,
    run_ctx: Optional[Dict[str, Any]] = None,
) -> dict[str, Any]:
    params_by_source = params_by_source or {}
    default_params = default_params or {}
    run_ctx = run_ctx or {}

    ordered_ids = sorted({sid for sid in source_ids if sid})
    packets_by_source: dict[str, list[dict[str, Any]]] = {}
    errors: dict[str, str] = {}
    source_results: list[dict[str, Any]] = []
    total_packets = 0
    started = time.perf_counter()

    for source_id in ordered_ids:
        source_started = time.perf_counter()
        params = dict(default_params)
        source_overrides = params_by_source.get(source_id)
        if isinstance(source_overrides, dict):
            params.update(source_overrides)
        try:
            packets = run_source_once(
                source_id=source_id,
                window=window,
                params=params,
                cache_dir=cache_dir,
                run_ctx=run_ctx,
            )
            packet_payloads = [packet.model_dump() for packet in packets]
            packets_by_source[source_id] = packet_payloads
            total_packets += len(packet_payloads)
            source_results.append(
                {
                    "source_id": source_id,
                    "status": "ok",
                    "packet_count": len(packet_payloads),
                    "duration_ms": round((time.perf_counter() - source_started) * 1000, 3),
                }
            )
        except Exception as exc:
            error_text = f"{type(exc).__name__}: {exc}"
            errors[source_id] = error_text
            source_results.append(
                {
                    "source_id": source_id,
                    "status": "error",
                    "packet_count": 0,
                    "error": error_text,
                    "duration_ms": round((time.perf_counter() - source_started) * 1000, 3),
                }
            )

    total_duration_ms = round((time.perf_counter() - started) * 1000, 3)
    succeeded = sum(1 for item in source_results if item.get("status") == "ok")
    failed = sum(1 for item in source_results if item.get("status") == "error")
    return {
        "window": window.model_dump(),
        "source_ids": ordered_ids,
        "packets_by_source": packets_by_source,
        "errors": errors,
        "source_results": source_results,
        "summary": {
            "total_sources": len(ordered_ids),
            "succeeded": succeeded,
            "failed": failed,
            "total_packets": total_packets,
            "duration_ms": total_duration_ms,
        },
        "ok": not errors,
    }
