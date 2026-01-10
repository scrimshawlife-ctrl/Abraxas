"""Deterministic intake scheduling for SourceAtlas."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, List

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.sources.atlas import build_source_atlas
from abraxas.temporal.normalize import normalize_timestamp


class CadenceEntry(BaseModel):
    source_id: str
    cadence: str
    next_run_utc: str


class CadencePlan(BaseModel):
    generated_at_utc: str
    entries: List[CadenceEntry] = Field(default_factory=list)
    provenance: Dict[str, str] = Field(default_factory=dict)


def _next_run(anchor: datetime, cadence: str) -> datetime:
    if cadence == "hourly":
        return anchor + timedelta(hours=1)
    if cadence == "daily":
        return anchor + timedelta(days=1)
    if cadence == "weekly":
        return anchor + timedelta(days=7)
    if cadence == "monthly":
        return anchor + timedelta(days=30)
    return anchor


def build_cadence_plan(anchor_ts: str, timezone_name: str = "UTC") -> CadencePlan:
    normalized = normalize_timestamp(anchor_ts, timezone_name)
    anchor = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    atlas = build_source_atlas()
    entries: List[CadenceEntry] = []

    for record in atlas.records:
        next_run = _next_run(anchor, record.cadence.value)
        entries.append(
            CadenceEntry(
                source_id=record.source_id,
                cadence=record.cadence.value,
                next_run_utc=next_run.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            )
        )

    entries_sorted = sorted(entries, key=lambda e: e.source_id)
    provenance = {
        "atlas_hash": atlas.atlas_hash(),
        "inputs_hash": sha256_hex(canonical_json({"anchor_ts": anchor_ts, "timezone": timezone_name})),
    }
    return CadencePlan(
        generated_at_utc=normalized,
        entries=entries_sorted,
        provenance=provenance,
    )
