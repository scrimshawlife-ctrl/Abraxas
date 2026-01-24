from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List


def _sorted_hits(hits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(
        hits,
        key=lambda h: (
            h.get("sub", ""),
            h.get("token", ""),
            h.get("source", ""),
            h.get("item_id", ""),
        ),
    )


def _cap_verified_hits(
    hits: List[Dict[str, Any]],
    clusters_by_item_id: Dict[str, str],
    *,
    per_token: int,
    per_cluster: int,
    total: int,
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    per_token_counts = Counter()
    per_cluster_counts = Counter()
    for h in _sorted_hits(hits):
        token = h.get("token", "")
        cluster = clusters_by_item_id.get(h.get("item_id", ""), "")
        if per_token_counts[token] >= per_token:
            continue
        if cluster and per_cluster_counts[cluster] >= per_cluster:
            continue
        out.append(h)
        per_token_counts[token] += 1
        if cluster:
            per_cluster_counts[cluster] += 1
        if len(out) >= total:
            break
    return out


def _scrub_fields(obj: Any, *, include_urls: bool) -> Any:
    if isinstance(obj, list):
        return [_scrub_fields(item, include_urls=include_urls) for item in obj]
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if not include_urls and k in {"url", "text"}:
                continue
            out[k] = _scrub_fields(v, include_urls=include_urls)
        return out
    return obj


def _scrub_rune_evidence_rows(domains: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove per-item evidence_rows from domain rune data (for psychonaut tier).

    Preserves: motif_stats, provenance (without input_hash details)
    Removes: evidence_rows, cluster_maps
    """
    scrubbed = {}
    for domain_id, data in domains.items():
        if not isinstance(data, dict):
            scrubbed[domain_id] = data
            continue

        cleaned = {}
        for k, v in data.items():
            # Remove per-item evidence rows for lower tiers
            if k in {"evidence_rows", "cluster_map", "item_to_cluster"}:
                continue
            # Summarize provenance
            if k == "provenance" and isinstance(v, dict):
                cleaned[k] = {
                    "rune_id": v.get("rune_id"),
                    "rune_version": v.get("rune_version"),
                    "schema_versions": v.get("schema_versions"),
                }
            else:
                cleaned[k] = v
        scrubbed[domain_id] = cleaned
    return scrubbed


def apply_tier(report: Dict[str, Any], *, tier: str, safe_export: bool, include_urls: bool) -> Dict[str, Any]:
    tier_norm = (tier or "psychonaut").lower()
    key_fp = report.get("key_fingerprint")
    schema_versions = report.get("schema_versions", {})
    base = {
        "date": report.get("date"),
        "version": report.get("version"),
        "schema_versions": schema_versions,
        "stats": report.get("stats", {}),
    }
    if key_fp:
        base["key_fingerprint"] = key_fp

    if tier_norm == "psychonaut":
        base["summary"] = {
            "high_tap_tokens": len(report.get("high_tap_tokens", [])),
            "tier2_hits": report.get("stats", {}).get("tier2_hits", 0),
            "pfdi_alerts": report.get("stats", {}).get("pfdi_alerts", 0),
        }
        base["high_tap_tokens"] = report.get("high_tap_tokens", [])[:10]
        sas_rows = report.get("sas", {}).get("rows", [])[:20]
        base["sas"] = {"rows": sas_rows}
        # For psychonaut: scrub rune evidence rows if present
        if "domains" in report:
            base["domains"] = _scrub_rune_evidence_rows(report.get("domains", {}))
        return base

    if tier_norm == "academic":
        clusters = report.get("clusters", {})
        clusters_by_item_id = clusters.get("by_item_id", {})
        capped_hits = _cap_verified_hits(
            report.get("verified_sub_anagrams", []),
            clusters_by_item_id,
            per_token=5,
            per_cluster=10,
            total=200,
        )
        base["run_id"] = report.get("run_id")
        base["verified_sub_anagrams"] = capped_hits
        base["sas"] = report.get("sas", {})
        base["clusters"] = clusters
        base["pfdi_alerts"] = report.get("pfdi_alerts", [])
        base["runtime_lexicon"] = report.get("runtime_lexicon", {})
        base["methods"] = {"sas_params": report.get("sas", {}).get("params", {})}
        return _scrub_fields(base, include_urls=(include_urls or not safe_export))

    enterprise = _scrub_fields(report, include_urls=include_urls)
    return enterprise
