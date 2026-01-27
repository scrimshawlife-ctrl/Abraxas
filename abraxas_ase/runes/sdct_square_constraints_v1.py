from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict
from typing import Any, Dict, List

from ..sdct.domains.square_constraints import SquareConstraintCartridge
from ..sdct.types import stable_hash


def _input_hash(payload: Dict[str, Any]) -> str:
    return stable_hash(payload)


def run(payload: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
    errors: List[str] = []
    items = payload.get("items")
    if not isinstance(items, list):
        errors.append("items must be a list")
    date = payload.get("date")
    if not isinstance(date, str):
        errors.append("date must be a string")
    event_keys = payload.get("event_keys_by_item_id")
    if not isinstance(event_keys, dict):
        errors.append("event_keys_by_item_id must be an object")

    if errors:
        return {
            "status": "not_computable",
            "errors": errors,
            "rune_id": "sdct.square_constraints.v1",
        }

    cartridge = SquareConstraintCartridge()
    descriptor = cartridge.descriptor()
    grid_params = {
        "letter_size": 5,
        "digit_size": 3,
        "include_diagonals": True,
        "max_motifs": 150,
    }

    input_hash = _input_hash({
        "items": items,
        "date": date,
        "event_keys_by_item_id": event_keys,
    })
    provenance = {
        "domain_id": descriptor.domain_id,
        "domain_version": descriptor.domain_version,
        "rune_id": "sdct.square_constraints.v1",
        "input_hash": input_hash,
        "schema_versions": {"sdct": "v0.1"},
        "grid_params": grid_params,
        "spec_id": "square_constraints.v1",
    }

    evidence_rows: List[Dict[str, Any]] = []
    motif_stats: Dict[str, Dict[str, Any]] = {}
    motif_sources = defaultdict(set)
    motif_events = defaultdict(set)
    motif_mentions = defaultdict(int)

    for item in items:
        item_id = str(item.get("id", ""))
        event_key = event_keys.get(item_id)
        if not event_key:
            return {
                "status": "not_computable",
                "errors": [f"missing event_key for item_id {item_id}"],
                "rune_id": "sdct.square_constraints.v1",
            }
        sym = cartridge.encode(item)
        motifs = cartridge.extract_motifs(sym)
        for ev in cartridge.emit_evidence(item, motifs, event_key):
            row = asdict(ev)
            row["provenance"] = provenance
            evidence_rows.append(row)
            motif_mentions[ev.motif_id] += ev.mentions
            motif_sources[ev.motif_id].add(ev.source)
            motif_events[ev.motif_id].add(ev.event_key)

    evidence_rows = sorted(
        evidence_rows,
        key=lambda r: (
            r.get("motif_id", ""),
            r.get("item_id", ""),
            r.get("source", ""),
        ),
    )

    for motif_id in sorted(motif_mentions.keys()):
        motif_stats[motif_id] = {
            "motif_id": motif_id,
            "mentions_total": motif_mentions[motif_id],
            "sources_count": len(motif_sources[motif_id]),
            "events_count": len(motif_events[motif_id]),
        }

    motif_stats_list = [motif_stats[m] for m in sorted(motif_stats.keys())]

    return {
        "status": "ok",
        "rune_id": "sdct.square_constraints.v1",
        "domain_id": descriptor.domain_id,
        "descriptor": asdict(descriptor),
        "provenance": provenance,
        "evidence_rows": evidence_rows,
        "motif_stats": motif_stats_list,
    }
