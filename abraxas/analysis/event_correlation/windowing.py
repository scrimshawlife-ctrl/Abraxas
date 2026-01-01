from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple


def parse_iso_z(ts: str) -> datetime:
    """
    Parse ISO8601 timestamps with optional trailing 'Z'.
    Deterministic, strict-ish parser for offline artifacts.
    """
    if not isinstance(ts, str) or not ts:
        raise ValueError("timestamp must be non-empty string")
    s = ts.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        # Assume UTC if naive (avoid locale dependence)
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def to_iso_z(dt: datetime) -> str:
    dt = dt.astimezone(timezone.utc).replace(microsecond=0)
    return dt.isoformat().replace("+00:00", "Z")


def envelope_timestamp_utc(envelope: Dict[str, Any]) -> str | None:
    """
    Best-effort artifact timestamp extraction.
    Prefers explicit created_at_utc; falls back to common window fields.
    """
    if isinstance(envelope.get("created_at_utc"), str) and envelope["created_at_utc"]:
        return envelope["created_at_utc"]

    # Common oracle envelope shape
    sig = envelope.get("oracle_signal", {}) if isinstance(envelope.get("oracle_signal"), dict) else {}
    win = sig.get("window", {}) if isinstance(sig.get("window"), dict) else {}
    for k in ("end_iso", "start_iso"):
        if isinstance(win.get(k), str) and win[k]:
            return win[k]

    return None


def stable_sort_envelopes(envelopes: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deterministic sort: (timestamp, artifact_id fallback stable), then canonical tie-breaker.
    """

    def key(env: Dict[str, Any]) -> Tuple[str, str]:
        ts = envelope_timestamp_utc(env) or ""
        aid = str(env.get("artifact_id") or env.get("run_id") or "")
        return (ts, aid)

    return sorted(list(envelopes), key=key)


@dataclass(frozen=True)
class Window:
    start_idx: int
    end_idx_exclusive: int


def rolling_windows(n: int, window_size: int) -> Iterator[Window]:
    """
    Yield rolling windows over indices [0..n).
    """
    if window_size <= 0:
        raise ValueError("window_size must be > 0")
    if n <= 0:
        return iter(())
    for start in range(0, n):
        end = min(n, start + window_size)
        yield Window(start_idx=start, end_idx_exclusive=end)


def window_bounds(envelopes: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute drift-report window fields: start/end artifact timestamps + count.
    """
    envs = list(envelopes)
    ts_list: List[datetime] = []
    for env in envs:
        ts = envelope_timestamp_utc(env)
        if ts is None:
            continue
        ts_list.append(parse_iso_z(ts))

    if not ts_list:
        start = end = None
    else:
        start = to_iso_z(min(ts_list))
        end = to_iso_z(max(ts_list))

    return {
        "start_artifact_ts": start,
        "end_artifact_ts": end,
        "artifact_count": len(envs),
    }

