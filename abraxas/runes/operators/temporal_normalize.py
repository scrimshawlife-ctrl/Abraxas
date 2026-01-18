"""ABX-Rune Operator: TEMPORAL_NORMALIZE."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.temporal.calendars import events_in_window
from abraxas.temporal.normalize import normalize_to_utc, window_to_utc
from abraxas.temporal.timezones import timezone_table


class TemporalNormalizeResult(BaseModel):
    shadow_only: bool = Field(True, description="Shadow-only enforcement")
    normalized_timestamp_utc: str
    timezone_snapshot: Dict[str, Any]
    calendar_events: List[Dict[str, Any]]
    not_computable_detail: Optional[Dict[str, Any]] = Field(
        None, description="Structured not_computable detail"
    )
    provenance: Dict[str, Any] = Field(default_factory=dict)


def apply_temporal_normalize(
    timestamp: str,
    timezone: Optional[str] = None,
    window: Optional[Dict[str, str]] = None,
    calendars: Optional[List[str]] = None,
    *,
    strict_execution: bool = False,
) -> Dict[str, Any]:
    if not timestamp:
        if strict_execution:
            raise NotImplementedError("TEMPORAL_NORMALIZE requires timestamp")
        return TemporalNormalizeResult(
            normalized_timestamp_utc="",
            timezone_snapshot={},
            calendar_events=[],
            not_computable_detail={
                "reason": "missing required inputs",
                "missing_inputs": ["timestamp"],
            },
            provenance={
                "inputs_hash": sha256_hex(canonical_json({"timestamp": None})),
                "tzdb_version": None,
            },
        ).model_dump()

    tz_name = timezone or "UTC"
    normalized = normalize_to_utc(timestamp, tz_name)
    tz_table = timezone_table()
    window = window or {"start_utc": normalized, "end_utc": normalized}
    if window.get("start_utc") and window.get("end_utc"):
        start_utc, end_utc = window_to_utc(window["start_utc"], window["end_utc"], tz_name)
        window = {"start_utc": start_utc, "end_utc": end_utc}
    events = events_in_window(window, calendars=calendars)

    provenance = {
        "inputs_hash": sha256_hex(
            canonical_json({"timestamp": timestamp, "timezone": tz_name, "window": window, "calendars": calendars})
        ),
        "tzdb_version": tz_table.get("version"),
    }

    return TemporalNormalizeResult(
        normalized_timestamp_utc=normalized,
        timezone_snapshot=tz_table,
        calendar_events=events,
        provenance=provenance,
    ).model_dump()
