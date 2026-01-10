"""Timezone table and DST windows (vendored snapshot)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def _snapshot_path() -> Path:
    base = Path(__file__).resolve().parents[2] / "data" / "tzdb"
    if base.exists():
        return base / "2025c.json"
    return Path(__file__).resolve().parents[2] / "data" / "temporal" / "iana_tzdb_2025c.json"


def timezone_table() -> Dict[str, Any]:
    payload = json.loads(_snapshot_path().read_text(encoding="utf-8"))
    return payload


def tzdb_version() -> str:
    return str(timezone_table().get("version"))


def list_timezones() -> List[str]:
    zones = timezone_table().get("zones") or {}
    return sorted(zones.keys())


def get_offset(tz_name: str, utc_iso: str) -> int:
    from datetime import datetime

    table = timezone_table()
    zones = table.get("zones") or {}
    zone = zones.get(tz_name)
    if zone is None:
        return 0
    if utc_iso.endswith("Z"):
        utc_iso = utc_iso[:-1] + "+00:00"
    ts = datetime.fromisoformat(utc_iso)
    std = _offset_minutes(zone.get("offset_std", "+00:00"))
    for window in zone.get("dst", []) or []:
        start = datetime.fromisoformat(window["start_utc"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(window["end_utc"].replace("Z", "+00:00"))
        if start <= ts < end:
            return _offset_minutes(window.get("offset", zone.get("offset_dst", "+00:00")))
    return std


def _offset_minutes(offset: str) -> int:
    sign = 1 if offset.startswith("+") else -1
    hours, minutes = offset[1:].split(":")
    return sign * (int(hours) * 60 + int(minutes))
