from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, List


@dataclass(frozen=True)
class HorizonBand:
    key: str  # "H1W", "H1M", "H6M", "H2Y", "H5Y"
    days: int
    half_life_days: int
    reevaluate_every_days: int


DEFAULT_BANDS: List[HorizonBand] = [
    HorizonBand("H1W", days=7, half_life_days=2, reevaluate_every_days=1),
    HorizonBand("H1M", days=30, half_life_days=7, reevaluate_every_days=3),
    HorizonBand("H6M", days=182, half_life_days=30, reevaluate_every_days=14),
    HorizonBand("H2Y", days=730, half_life_days=90, reevaluate_every_days=30),
    HorizonBand("H5Y", days=1825, half_life_days=180, reevaluate_every_days=60),
]


def bands_index() -> Dict[str, HorizonBand]:
    return {b.key: b for b in DEFAULT_BANDS}


def next_review(ts_iso: str, band_key: str) -> str:
    b = bands_index()[band_key]
    dt = (
        datetime.fromisoformat(ts_iso.replace("Z", "+00:00"))
        if "Z" in ts_iso
        else datetime.fromisoformat(ts_iso)
    )
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    nxt = dt + timedelta(days=int(b.reevaluate_every_days))
    return nxt.replace(microsecond=0).isoformat()
