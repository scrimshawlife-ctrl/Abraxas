"""Acquisition transport helpers for bulk/surgical/cache-only fetches."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from abraxas.core.canonical import sha256_hex
from abraxas.osh.types import OSHFetchJob, RawFetchArtifact
from abraxas.storage.cas import CASRef, CASStore


@dataclass(frozen=True)
class FetchResult:
    url: str
    status_code: int
    content_type: str
    body: bytes
    raw_ref: CASRef
    method: str
    decodo_used: bool
    artifact: Optional[RawFetchArtifact] = None


def acquire_bulk(
    *,
    url: str,
    source_id: str,
    run_id: str,
    cas_store: CASStore,
    recorded_at_utc: str | None = None,
    budget: Dict[str, Any] | None = None,
) -> FetchResult:
    from abraxas.osh.transport import direct_http_fetch

    job = _build_job(url=url, source_id=source_id, run_id=run_id, budget=budget)
    artifact = direct_http_fetch(job, out_raw_dir="out/osh/raw")
    body = _read_body(artifact)
    raw_ref = cas_store.store_bytes(
        body,
        subdir="raw",
        suffix=".bin",
        url=url,
        recorded_at_utc=recorded_at_utc,
        meta={"source_id": source_id, "method": "bulk"},
    )
    return FetchResult(
        url=url,
        status_code=artifact.status_code,
        content_type=artifact.content_type,
        body=body,
        raw_ref=raw_ref,
        method="bulk",
        decodo_used=False,
        artifact=artifact,
    )


def acquire_surgical(
    *,
    url: str,
    source_id: str,
    run_id: str,
    cas_store: CASStore,
    recorded_at_utc: str | None = None,
    budget: Dict[str, Any] | None = None,
) -> FetchResult:
    from abraxas.osh.decodo_client import decodo_fetch

    job = _build_job(url=url, source_id=source_id, run_id=run_id, budget=budget)
    artifact = decodo_fetch(job, out_raw_dir="out/osh/raw")
    body = _read_body(artifact)
    raw_ref = cas_store.store_bytes(
        body,
        subdir="raw",
        suffix=".bin",
        url=url,
        recorded_at_utc=recorded_at_utc,
        meta={"source_id": source_id, "method": "surgical"},
    )
    return FetchResult(
        url=url,
        status_code=artifact.status_code,
        content_type=artifact.content_type,
        body=body,
        raw_ref=raw_ref,
        method="surgical",
        decodo_used=True,
        artifact=artifact,
    )


def acquire_cache_only(
    *,
    url: str,
    cas_store: CASStore,
) -> FetchResult | None:
    entry = cas_store.lookup_url(url)
    if not entry:
        return None
    body = Path(entry.path).read_bytes()
    raw_ref = CASRef(
        content_hash=entry.content_hash,
        path=entry.path,
        bytes=len(body),
        subdir=entry.subdir,
        suffix=entry.suffix,
    )
    return FetchResult(
        url=url,
        status_code=200,
        content_type="application/octet-stream",
        body=body,
        raw_ref=raw_ref,
        method="cache_only",
        decodo_used=False,
        artifact=None,
    )


def _build_job(url: str, source_id: str, run_id: str, budget: Dict[str, Any] | None) -> OSHFetchJob:
    job_id = sha256_hex(f"{run_id}:{source_id}:{url}")[:16]
    return OSHFetchJob(
        job_id=job_id,
        run_id=run_id,
        action_id=f"manifest:{job_id}",
        url=url,
        method="GET",
        params={},
        source_label=source_id,
        vector_node_id=None,
        allowlist_source_id=source_id,
        budget=budget or {"max_requests": 1, "max_bytes": 5_000_000, "timeout_s": 60},
        provenance={"acquisition": "manifest_first"},
    )


def _read_body(artifact: RawFetchArtifact) -> bytes:
    from pathlib import Path

    return Path(artifact.body_path).read_bytes()
