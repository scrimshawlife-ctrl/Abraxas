"""Manifest discovery engine (budgeted, deterministic)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from abraxas.acquisition.manifest_parse import (
    parse_index_html,
    parse_json_listing,
    parse_rss,
    parse_sitemap_xml,
)
from abraxas.acquisition.manifest_schema import ManifestArtifact, ManifestProvenance
from abraxas.acquisition.perf_ledger import PerfLedger
from abraxas.acquisition.transport import acquire_bulk, acquire_cache_only, acquire_surgical
from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.policy.utp import PortfolioTuningIR
from abraxas.sources import get_source
from abraxas.storage.cas import CASStore


@dataclass(frozen=True)
class ManifestDiscoveryResult:
    manifest: ManifestArtifact
    raw_ref: Dict[str, Any]
    parsed_ref: Dict[str, Any]


def discover_manifest(
    *,
    source_id: str,
    seed_targets: List[str] | None,
    run_ctx: Dict[str, Any],
    budgets: PortfolioTuningIR,
    cas_store: CASStore | None = None,
    perf_ledger: PerfLedger | None = None,
    allow_decodo: bool = True,
) -> ManifestDiscoveryResult:
    cas_store = cas_store or CASStore()
    perf_ledger = perf_ledger or PerfLedger()
    now_utc = run_ctx.get("now_utc") or "1970-01-01T00:00:00Z"

    seeds = _resolve_seeds(source_id, seed_targets)
    if not seeds:
        raise ValueError("Manifest discovery requires seed targets or SourceAtlas manifest_seeds")

    seed_entries = []
    urls_union: List[str] = []
    decodo_remaining = budgets.ubv.decodo_policy.max_requests

    for seed in sorted(seeds):
        fetch_result, reason_code = _fetch_seed(
            seed,
            source_id,
            run_ctx,
            cas_store,
            allow_decodo and budgets.ubv.decodo_policy.manifest_only,
            decodo_remaining,
        )
        if fetch_result is None:
            seed_entries.append(
                {
                    "seed_url": seed,
                    "kind": "UNKNOWN",
                    "urls": [],
                    "error": reason_code or "fetch_failed",
                }
            )
            continue

        if fetch_result.decodo_used:
            decodo_remaining = max(0, decodo_remaining - 1)

        raw_text = _decode_text(fetch_result.body)
        kind, parsed_urls, parse_notes = _parse_manifest(raw_text)
        urls_union.extend(parsed_urls)

        seed_entries.append(
            {
                "seed_url": seed,
                "kind": kind,
                "urls": parsed_urls,
                "raw_hash": fetch_result.raw_ref.content_hash,
                "raw_bytes": fetch_result.raw_ref.bytes,
                "cache_path": fetch_result.raw_ref.path,
                "retrieval_method": fetch_result.method,
                "decodo_used": fetch_result.decodo_used,
                "reason_code": reason_code,
                "parse_notes": parse_notes,
            }
        )

        perf_ledger.record(
            {
                "ts": now_utc,
                "event": "manifest_fetch",
                "source_id": source_id,
                "seed_url": seed,
                "bytes": fetch_result.raw_ref.bytes,
                "method": fetch_result.method,
                "decodo_used": fetch_result.decodo_used,
                "reason_code": reason_code,
            }
        )

    urls = sorted(set(urls_union))
    kind = _combine_kinds([entry.get("kind") for entry in seed_entries])
    parse_hash = sha256_hex(canonical_json({"kind": kind, "urls": urls}))
    raw_hash = sha256_hex(canonical_json([entry.get("raw_hash") for entry in seed_entries]))

    manifest_metadata = {
        "seed_manifests": seed_entries,
        "seed_count": len(seed_entries),
    }

    parsed_ref = cas_store.store_json(
        {
            "source_id": source_id,
            "kind": kind,
            "urls": urls,
            "metadata": manifest_metadata,
            "retrieved_at_utc": now_utc,
        },
        subdir="manifests",
        suffix=".json",
        recorded_at_utc=now_utc,
        meta={"source_id": source_id, "manifest": True},
    )

    provenance = ManifestProvenance(
        retrieval_method=_derive_retrieval_method(seed_entries),
        decodo_used=any(e.get("decodo_used") for e in seed_entries),
        reason_code=None,
        raw_hash=raw_hash,
        parse_hash=parse_hash,
        cache_path=parsed_ref.path,
    )

    manifest = ManifestArtifact.build(
        source_id=source_id,
        retrieved_at_utc=now_utc,
        kind=kind,
        urls=urls,
        metadata=manifest_metadata,
        provenance=provenance,
    )

    return ManifestDiscoveryResult(
        manifest=manifest,
        raw_ref={"hash": raw_hash, "count": len(seed_entries)},
        parsed_ref=parsed_ref.to_dict(),
    )


def _resolve_seeds(source_id: str, seed_targets: List[str] | None) -> List[str]:
    if seed_targets:
        return list(seed_targets)
    source = get_source(source_id)
    if not source:
        return []
    seeds = list(source.manifest_seeds or []) + list(source.bulk_endpoints or [])
    return [seed for seed in seeds if seed]


def _fetch_seed(
    seed: str,
    source_id: str,
    run_ctx: Dict[str, Any],
    cas_store: CASStore,
    allow_decodo: bool,
    decodo_remaining: int,
) -> Tuple[Any | None, Optional[str]]:
    cached = acquire_cache_only(url=seed, cas_store=cas_store)
    if cached:
        return cached, "cache_hit"

    try:
        result = acquire_bulk(
            url=seed,
            source_id=source_id,
            run_id=run_ctx.get("run_id", "manifest"),
            cas_store=cas_store,
            recorded_at_utc=run_ctx.get("now_utc"),
        )
        return result, None
    except Exception as exc:
        bulk_reason = f"bulk_failed:{type(exc).__name__}"

    if allow_decodo and decodo_remaining > 0:
        try:
            result = acquire_surgical(
                url=seed,
                source_id=source_id,
                run_id=run_ctx.get("run_id", "manifest"),
                cas_store=cas_store,
                recorded_at_utc=run_ctx.get("now_utc"),
            )
            return result, "decodo"
        except Exception as exc:
            return None, f"surgical_failed:{type(exc).__name__}:{bulk_reason}"

    return None, bulk_reason


def _parse_manifest(raw_text: str) -> Tuple[str, List[str], Optional[str]]:
    text = raw_text.strip()
    if not text:
        return "UNKNOWN", [], "empty"

    if _looks_like_sitemap(text):
        urls = parse_sitemap_xml(text)
        return "SITEMAP", urls, None if urls else "sitemap_parse_failed"
    if _looks_like_rss(text):
        urls = parse_rss(text)
        return "RSS_INDEX", urls, None if urls else "rss_parse_failed"

    urls = parse_json_listing(text)
    if urls:
        return "API_LISTING", urls, None

    urls = parse_index_html(text)
    if urls:
        return "INDEX_HTML", urls, None

    return "UNKNOWN", [], "unrecognized_format"


def _looks_like_sitemap(text: str) -> bool:
    return "<urlset" in text or "<sitemapindex" in text


def _looks_like_rss(text: str) -> bool:
    return "<rss" in text or "<feed" in text


def _decode_text(data: bytes) -> str:
    for encoding in ("utf-8", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="ignore")


def _combine_kinds(kinds: List[str]) -> str:
    unique = sorted({k for k in kinds if k})
    return unique[0] if len(unique) == 1 else "UNKNOWN"


def _derive_retrieval_method(seed_entries: List[Dict[str, Any]]) -> str:
    methods = {entry.get("retrieval_method") for entry in seed_entries if entry.get("retrieval_method")}
    if "surgical" in methods:
        return "surgical"
    if "bulk" in methods:
        return "bulk"
    return "cache_only"
