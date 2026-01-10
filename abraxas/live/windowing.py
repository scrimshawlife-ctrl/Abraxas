"""Live window computation utilities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List


@dataclass(frozen=True)
class LiveWindowConfig:
    window_size: str
    step_size: str
    alignment: str = "utc_midnight"
    retention: int = 30


@dataclass(frozen=True)
class LiveWindow:
    start_utc: str
    end_utc: str


def stable_now_utc(run_ctx) -> str:
    now = getattr(run_ctx, "now_utc", None)
    if not now:
        raise ValueError("run_ctx.now_utc must be provided for live window computation")
    return str(now)


def compute_live_windows(now_utc: str, config: LiveWindowConfig) -> List[LiveWindow]:
    now_dt = _parse_iso(now_utc)
    aligned = _align_now(now_dt, config.alignment)
    window_delta = _parse_duration(config.window_size)
    step_delta = _parse_duration(config.step_size)
    windows: List[LiveWindow] = []
    current_end = aligned
    for _ in range(max(config.retention, 0)):
        start = current_end - window_delta
        windows.append(LiveWindow(start_utc=_format_iso(start), end_utc=_format_iso(current_end)))
        current_end = current_end - step_delta
    return list(reversed(windows))


def _align_now(now_dt: datetime, alignment: str) -> datetime:
    if alignment == "utc_midnight":
        return datetime(now_dt.year, now_dt.month, now_dt.day, tzinfo=timezone.utc)
    return now_dt


def _parse_duration(value: str) -> timedelta:
    value = value.strip().lower()
    if value.endswith("d"):
        return timedelta(days=int(value[:-1]))
    if value.endswith("h"):
        return timedelta(hours=int(value[:-1]))
    raise ValueError(f"Unsupported duration format: {value}")


def _parse_iso(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


def _format_iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
