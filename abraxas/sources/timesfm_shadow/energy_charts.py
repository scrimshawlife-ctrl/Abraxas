"""Parse Energy Charts price snapshots into a history window."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Mapping

from abraxas.sources.timesfm_shadow.constants import BZN, DEFAULT_WINDOW_N
from abraxas.sources.timesfm_shadow.packets import HistoryBlock


def parse_energy_charts_price(
    payload: Mapping[str, object],
    *,
    window_n: int = DEFAULT_WINDOW_N,
    bzn: str = BZN,
) -> HistoryBlock:
    if bzn != BZN:
        raise ValueError(f"this slice accepts bzn={BZN} only")
    if window_n < 1:
        raise ValueError("window_n must be >= 1")
    stamps = _as_list(payload.get("unix_seconds"), "unix_seconds")
    prices = _as_list(payload.get("price"), "price")
    if len(stamps) != len(prices):
        raise ValueError("unix_seconds and price must have equal length")
    paired = [_pair(stamp, price) for stamp, price in zip(stamps, prices)]
    kept = [item for item in paired if item is not None]
    if not kept:
        raise ValueError("energy charts history is empty after null filter")
    clipped = kept[-window_n:]
    timestamps = [item[0] for item in clipped]
    values = [item[1] for item in clipped]
    return HistoryBlock(timestamps=timestamps, values=values, window_n=len(values))


def _as_list(raw: object, field: str) -> list[object]:
    if not isinstance(raw, list) or not raw:
        raise ValueError(f"{field} must be a non-empty list")
    return list(raw)


def _pair(stamp: object, price: object) -> tuple[str, float] | None:
    if price is None:
        return None
    if isinstance(price, bool) or not isinstance(price, (int, float)):
        raise ValueError("price entries must be numeric")
    if isinstance(stamp, bool) or not isinstance(stamp, (int, float)):
        raise ValueError("unix_seconds entries must be numeric")
    instant = datetime.fromtimestamp(int(stamp), tz=timezone.utc)
    return instant.strftime("%Y-%m-%dT%H:%M:%SZ"), float(price)
