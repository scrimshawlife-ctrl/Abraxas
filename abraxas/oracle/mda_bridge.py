from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from abraxas.mda.types import sha256_hex, stable_json_dumps


def _normalize_payload(payload: Dict[str, Any]) -> tuple[Optional[str], Dict[str, Any]]:
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    bundle_id = payload.get("bundle_id")
    vectors = payload.get("vectors")
    if not isinstance(vectors, dict):
        raise ValueError("payload must include 'vectors' object (bundle or vectors-only)")
    return (bundle_id if isinstance(bundle_id, str) else None, vectors)


def _filter_vectors(
    vectors: Dict[str, Any],
    *,
    domains: Optional[Tuple[str, ...]],
    subdomains: Optional[Tuple[str, ...]],
) -> Dict[str, Any]:
    if domains is None and subdomains is None:
        return vectors

    allowed_domains = set(domains or [])
    # subdomains are provided as "domain:subdomain"
    allowed_pairs: set[tuple[str, str]] = set()
    if subdomains:
        for item in subdomains:
            if ":" not in item:
                continue
            d, s = item.split(":", 1)
            d = d.strip()
            s = s.strip()
            if d and s:
                allowed_pairs.add((d, s))

    out: Dict[str, Any] = {}
    for domain, submap in (vectors or {}).items():
        if not isinstance(domain, str):
            continue
        if domains is not None and domain not in allowed_domains:
            continue
        if not isinstance(submap, dict):
            continue

        if subdomains is None:
            out[domain] = submap
            continue

        kept: Dict[str, Any] = {}
        for subdomain, blob in submap.items():
            if not isinstance(subdomain, str):
                continue
            if (domain, subdomain) in allowed_pairs:
                kept[subdomain] = blob
        if kept:
            out[domain] = kept

    return out


def run_mda_for_oracle(
    *,
    env: str,
    run_at_iso: str,
    seed: int,
    abraxas_version: str,
    domains: Optional[Tuple[str, ...]],
    subdomains: Optional[Tuple[str, ...]],
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Minimal deterministic MDA shim for the batch oracle practice loop.

    It normalizes bundle/vectors-only payloads and applies deterministic filtering.
    """

    bundle_id, vectors = _normalize_payload(payload)
    vectors_slice = _filter_vectors(vectors, domains=domains, subdomains=subdomains)
    payload_hash = sha256_hex(stable_json_dumps(payload))

    return {
        "mda": {
            "meta": {
                "env": str(env),
                "run_at": str(run_at_iso),
                "seed": int(seed),
                "abraxas_version": str(abraxas_version),
                "payload_hash": payload_hash,
            },
            "bundle_id": bundle_id,
            "domains": list(domains) if domains else [],
            "subdomains": list(subdomains) if subdomains else [],
            "vectors": vectors_slice,
        }
    }

