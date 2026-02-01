"""
ABX-Runes Adapter: sdct.digit.v1

Rune wrapper for DigitMotifCartridge.
Deterministic evidence emission with provenance tracking.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Optional

from ..domains.digit_motif import create_digit_cartridge
from ..domains.types import RawItem
from ..keyed import keyed_id, read_key_or_none
from ..provenance import sha256_hex, stable_json_dumps


RUNE_ID = "sdct.digit.v1"
DOMAIN_ID = "digit.v1"


class NotComputableError(Exception):
    """Raised when rune cannot compute due to missing required inputs."""

    def __init__(self, field: str, reason: str):
        self.field = field
        self.reason = reason
        super().__init__(f"Not computable: {field} - {reason}")


def _validate_items(items: List[Dict[str, Any]]) -> List[RawItem]:
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
    title = item.title.strip().lower()
    title = "".join(ch for ch in title if ch.isalnum() or ch.isspace())
    title = " ".join(title.split())
    raw = f"cluster|{item.source}|{title[:64]}"

    if hmac_key:
        return keyed_id(hmac_key, raw, n=32)
    return sha256_hex(raw.encode("utf-8"))


def _input_hash(items: List[RawItem], params: Dict[str, Any]) -> str:
    payload = {
        "items": [item.to_dict() for item in items],
        "params": params,
    }
    return sha256_hex(stable_json_dumps(payload).encode("utf-8"))


def _coerce_int(value: Any, default: int) -> int:
    return value if isinstance(value, int) else default


def _build_provenance(
    ctx: Dict[str, Any],
    descriptor: Any,
    input_hash: str,
    date: Optional[str],
) -> Dict[str, Any]:
    return {
        "domain_id": getattr(descriptor, "domain_id", DOMAIN_ID),
        "domain_version": getattr(descriptor, "domain_version", "unknown"),
        "rune_id": ctx.get("rune_id", RUNE_ID),
        "input_hash": input_hash,
        "schema_versions": {"sdct": "v0.1"},
        "run_id": ctx.get("run_id"),
        "date": date,
    }


def invoke(
    payload: Dict[str, Any],
    ctx: Dict[str, Any],
) -> Dict[str, Any]:
    items_raw = payload.get("items")
    params = payload.get("params", {}) or {}
    date = payload.get("date")

    if items_raw is None:
        return {
            "evidence_rows": [],
            "motif_stats": [],
            "not_computable": {
                "field": "items",
                "reason": "items field is required",
            },
            "provenance": _build_provenance(ctx, None, "", date),
        }

    try:
        items = _validate_items(items_raw)
    except NotComputableError as err:
        return {
            "evidence_rows": [],
            "motif_stats": [],
            "not_computable": {
                "field": err.field,
                "reason": err.reason,
            },
            "provenance": _build_provenance(ctx, None, "", date),
        }

    min_len = _coerce_int(params.get("min_len"), 3)
    max_len = _coerce_int(params.get("max_len"), 8)
    additional_patterns = params.get("additional_patterns", [])
    if not isinstance(additional_patterns, list):
        additional_patterns = []
    additional_patterns = frozenset(str(p) for p in additional_patterns)

    cartridge = create_digit_cartridge(
        min_len=min_len,
        max_len=max_len,
        additional_patterns=additional_patterns,
    )
    descriptor = cartridge.descriptor()

    items_sorted = sorted(items, key=lambda x: (x.published_at, x.source, x.id))
    input_hash = ctx.get("input_hash") or _input_hash(items_sorted, params)

    hmac_key = read_key_or_none()
    evidence_rows: List[Dict[str, Any]] = []
    motif_mentions: Dict[str, int] = {}
    motif_sources = defaultdict(set)
    motif_events = defaultdict(set)

    for item in items_sorted:
        event_key = _cluster_key(item, hmac_key)
        evidence_list = cartridge.process_item(item, event_key)
        for ev in evidence_list:
            row = ev.to_dict()
            row["provenance"] = {
                "rune_id": ctx.get("rune_id", RUNE_ID),
                "input_hash": input_hash,
                "run_id": ctx.get("run_id"),
            }
            evidence_rows.append(row)
            motif_id = row.get("motif_id", "")
            motif_mentions[motif_id] = motif_mentions.get(motif_id, 0) + int(
                row.get("mentions", 0)
            )
            motif_sources[motif_id].add(row.get("source", ""))
            motif_events[motif_id].add(row.get("event_key", ""))

    evidence_rows = sorted(
        evidence_rows,
        key=lambda r: (r.get("motif_id", ""), r.get("item_id", ""), r.get("source", "")),
    )

    motif_stats = []
    for motif_id in sorted(motif_mentions.keys()):
        motif_stats.append(
            {
                "motif_id": motif_id,
                "mentions_total": motif_mentions[motif_id],
                "sources_count": len(motif_sources[motif_id]),
                "events_count": len(motif_events[motif_id]),
            }
        )

    provenance = _build_provenance(ctx, descriptor, input_hash, date)

    return {
        "evidence_rows": evidence_rows,
        "motif_stats": motif_stats,
        "provenance": provenance,
        "not_computable": None,
    }
