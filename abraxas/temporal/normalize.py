"""Temporal normalization utilities."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from abraxas.temporal.timezones import get_offset, timezone_table


def _parse_iso(ts: str) -> datetime:
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    return datetime.fromisoformat(ts)


def _offset_to_timedelta(offset: str) -> timedelta:
    sign = 1 if offset.startswith("+") else -1
    hours, minutes = offset[1:].split(":")
    return sign * timedelta(hours=int(hours), minutes=int(minutes))


def _tz_offset(tz_name: str, ts: datetime) -> timedelta:
    table = timezone_table()
    zones = table.get("zones") or {}
    zone = zones.get(tz_name)
    if zone is None:
        return timedelta(0)
    std_offset = _offset_to_timedelta(zone.get("offset_std", "+00:00"))
    if ts.tzinfo is None:
        ts_utc = ts.replace(tzinfo=timezone(std_offset)).astimezone(timezone.utc)
    else:
        ts_utc = ts.astimezone(timezone.utc)
    dst_windows = zone.get("dst", [])
    for window in dst_windows:
        start = _parse_iso(window["start_utc"])
        end = _parse_iso(window["end_utc"])
        if start <= ts_utc < end:
            return _offset_to_timedelta(window.get("offset", zone.get("offset_dst", "+00:00")))
    return std_offset


def normalize_to_utc(dt_str: str, tz_name: Optional[str] = None) -> str:
    dt = _parse_iso(dt_str)
    if dt.tzinfo is None:
        tz_name = tz_name or "UTC"
        offset_minutes = get_offset(tz_name, dt.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"))
        dt = dt.replace(tzinfo=timezone(timedelta(minutes=offset_minutes)))
    dt_utc = dt.astimezone(timezone.utc)
    return dt_utc.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def window_to_utc(start_iso: str, end_iso: str, tz_name: Optional[str] = None) -> tuple[str, str]:
    return normalize_to_utc(start_iso, tz_name), normalize_to_utc(end_iso, tz_name)


def stable_now_utc(run_ctx: Optional[dict] = None) -> str:
    run_ctx = run_ctx or {}
    ts = run_ctx.get("timestamp") or run_ctx.get("run_at") or "1970-01-01T00:00:00Z"
    return normalize_to_utc(str(ts), run_ctx.get("timezone") or "UTC")


def normalize_timestamp(ts: str, tz_name: Optional[str] = None) -> str:
    return normalize_to_utc(ts, tz_name)
