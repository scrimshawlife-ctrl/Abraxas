"""
ABX-Runes Adapter: sdct.text_subword.v1

Rune wrapper for TextSubwordCartridge.
Enforces schema validation, deterministic ordering, and provenance tracking.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional

from ..domains.text_subword import TextSubwordCartridge
from ..domains.types import RawItem
from ..keyed import keyed_id, read_key_or_none
from ..lexicon import build_default_lexicon
from ..lexicon_runtime import load_canary_words
from ..provenance import sha256_hex, stable_json_dumps
from ..sas import SASParams, compute_sas_for_sub
from ..scoring import stable_round


RUNE_ID = "sdct.text_subword.v1"
DOMAIN_ID = "text.subword.v1"


class NotComputableError(Exception):
    """Raised when rune cannot compute due to missing required inputs."""

    def __init__(self, field: str, reason: str):
        self.field = field
        self.reason = reason
        super().__init__(f"Not computable: {field} - {reason}")


def _validate_items(items: List[Dict[str, Any]]) -> List[RawItem]:
    """Validate and convert items to RawItem objects."""
    if not items:
        raise NotComputableError("items", "items list is empty")

    required_keys = {"id", "source", "published_at", "title", "text"}
    validated = []

    for i, item in enumerate(items):
        if not isinstance(item, dict):
            raise NotComputableError("items", f"items[{i}] is not a dict")

        missing = required_keys - set(item.keys())
        if missing:
            raise NotComputableError("items", f"items[{i}] missing keys: {sorted(missing)}")

        validated.append(RawItem.from_dict(item))

    return validated


def _cluster_key(item: RawItem, hmac_key: Optional[bytes]) -> str:
    """
    Compute deterministic cluster key for an item.

    Same logic as engine.py _cluster_key for consistency.
    """
    title = item.title.strip().lower()
    title = "".join(ch for ch in title if ch.isalnum() or ch.isspace())
    title = " ".join(title.split())
    raw = f"cluster|{item.source}|{title[:64]}"

    if hmac_key:
        return keyed_id(hmac_key, raw, n=32)
    return sha256_hex(raw.encode("utf-8"))


def invoke(
    payload: Dict[str, Any],
    ctx: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Invoke the text.subword.v1 rune.

    Args:
        payload: {
            "items": List[dict],           # Required: items to process
            "params": dict,                # Optional: domain params
            "lanes_dir": str | None,       # Optional: path to lanes directory
        }
        ctx: {
            "rune_id": str,
            "input_hash": str,
            "run_id": str | None,
            "date": str,
            "tier": str,
            "key_fingerprint": str | None,
        }

    Returns:
        {
            "evidence_rows": List[dict],
            "motif_stats": List[dict],
            "provenance": dict,
            "not_computable": None | dict,
        }
    """
    # Extract payload fields
    items_raw = payload.get("items")
    params = payload.get("params", {})
    lanes_dir = payload.get("lanes_dir")

    # Validate required inputs
    if items_raw is None:
        return {
            "evidence_rows": [],
            "motif_stats": [],
            "not_computable": {
                "field": "items",
                "reason": "items field is required",
            },
            "provenance": _build_provenance(ctx, None),
        }

    try:
        items = _validate_items(items_raw)
    except NotComputableError as e:
        return {
            "evidence_rows": [],
            "motif_stats": [],
            "not_computable": {
                "field": e.field,
                "reason": e.reason,
            },
            "provenance": _build_provenance(ctx, None),
        }

    # Build cartridge with params
    lexicon = build_default_lexicon()
    canary_subwords = frozenset()

    if lanes_dir:
        from pathlib import Path
        try:
            canary_subwords = frozenset(load_canary_words(Path(lanes_dir)))
        except Exception:
            pass  # Non-fatal: proceed without canary words

    min_token_len = params.get("min_token_len", 4)
    min_sub_len = params.get("min_sub_len", 3)

    cartridge = TextSubwordCartridge(
        lexicon=lexicon,
        canary_subwords=canary_subwords,
        min_token_len=min_token_len,
        min_sub_len=min_sub_len,
    )

    # Get HMAC key for keyed IDs
    hmac_key = read_key_or_none()

    # Process all items
    all_evidence: List[Dict[str, Any]] = []
    item_to_cluster: Dict[str, str] = {}

    # Deterministic ordering by (published_at, source, id)
    items_sorted = sorted(items, key=lambda x: (x.published_at, x.source, x.id))

    for item in items_sorted:
        cluster_key = _cluster_key(item, hmac_key)
        item_to_cluster[item.id] = cluster_key

        # Process through cartridge
        evidence_list = cartridge.process_item(item, cluster_key)

        for ev in evidence_list:
            row = ev.to_dict()
            # Add provenance to each row
            row["provenance"] = {
                "rune_id": ctx.get("rune_id", RUNE_ID),
                "input_hash": ctx.get("input_hash", ""),
                "run_id": ctx.get("run_id"),
            }
            all_evidence.append(row)

    # Compute aggregated motif stats (SAS)
    motif_stats = _compute_motif_stats(all_evidence, item_to_cluster, lexicon)

    # Build runtime lexicon hash
    runtime_hash = sha256_hex(
        stable_json_dumps({
            "core_count": len(lexicon.subwords),
            "canary_count": len(canary_subwords),
            "stopwords_count": len(lexicon.stopwords),
        }).encode("utf-8")
    )

    provenance = _build_provenance(ctx, runtime_hash)

    return {
        "evidence_rows": all_evidence,
        "motif_stats": motif_stats,
        "provenance": provenance,
        "not_computable": None,
    }


def _compute_motif_stats(
    evidence_rows: List[Dict[str, Any]],
    item_to_cluster: Dict[str, str],
    lexicon: Any,
) -> List[Dict[str, Any]]:
    """Compute aggregated motif statistics (SAS)."""
    # Aggregate by motif_id
    motif_mentions: Counter = Counter()
    motif_sources: Dict[str, set] = defaultdict(set)
    motif_events: Dict[str, set] = defaultdict(set)
    motif_lane: Dict[str, str] = {}
    motif_tap_max: Dict[str, float] = defaultdict(float)

    for row in evidence_rows:
        motif_id = row["motif_id"]
        motif_mentions[motif_id] += row.get("mentions", 1)
        motif_sources[motif_id].add(row["source"])
        motif_events[motif_id].add(row["event_key"])

        if "lane" in row.get("tags", {}):
            motif_lane[motif_id] = row["tags"]["lane"]

        tap = row.get("signals", {}).get("tap", 0.0)
        if tap > motif_tap_max[motif_id]:
            motif_tap_max[motif_id] = tap

    # Compute SAS for each motif
    sas_params = SASParams()
    stats: List[Dict[str, Any]] = []

    for motif_id in sorted(motif_mentions.keys()):
        # Extract motif_text from motif_id (format: domain_id:motif_text)
        parts = motif_id.split(":", 1)
        motif_text = parts[1] if len(parts) > 1 else motif_id

        mentions = motif_mentions[motif_id]
        sources_count = len(motif_sources[motif_id])
        events_count = len(motif_events[motif_id])

        sas = compute_sas_for_sub(
            mentions=mentions,
            sources_count=sources_count,
            events_count=events_count,
            sub_len=len(motif_text),
            params=sas_params,
        )

        stats.append({
            "domain_id": DOMAIN_ID,
            "motif_id": motif_id,
            "motif_text": motif_text,
            "lane": motif_lane.get(motif_id, "candidate"),
            "mentions_total": mentions,
            "sources_count": sources_count,
            "events_count": events_count,
            "sas": sas,
            "tap_max": stable_round(motif_tap_max[motif_id]),
        })

    # Deterministic ordering
    return sorted(stats, key=lambda x: (x["lane"], x["motif_id"]))


def _build_provenance(
    ctx: Dict[str, Any],
    runtime_hash: Optional[str],
) -> Dict[str, Any]:
    """Build provenance envelope."""
    return {
        "rune_id": ctx.get("rune_id", RUNE_ID),
        "rune_version": ctx.get("rune_version", "1.0.0"),
        "input_hash": ctx.get("input_hash", ""),
        "run_id": ctx.get("run_id"),
        "date": ctx.get("date"),
        "tier": ctx.get("tier", "psychonaut"),
        "key_fingerprint": ctx.get("key_fingerprint"),
        "runtime_lexicon_hash": runtime_hash,
        "schema_versions": {
            "input": "sdct.domain_params.v0",
            "output": "sdct.evidence_row.v0",
        },
    }
