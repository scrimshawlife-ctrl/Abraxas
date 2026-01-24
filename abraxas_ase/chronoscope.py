from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from .provenance import stable_json_dumps


@dataclass(frozen=True)
class DayPoint:
    date: str
    run_id: str | None
    counts: Dict[str, Any]
    top_tap: List[Dict[str, Any]]
    top_sas: List[Dict[str, Any]]
    lane_counts: Dict[str, int]
    pfdi_alerts_count: int
    pack_hash: str | None


@dataclass(frozen=True)
class ChronoscopeState:
    version: int
    key_fingerprint: str | None
    series: List[DayPoint]


def _daypoint_from_dict(obj: Dict[str, Any]) -> DayPoint:
    return DayPoint(
        date=str(obj.get("date", "")),
        run_id=obj.get("run_id"),
        counts=dict(obj.get("counts", {})),
        top_tap=list(obj.get("top_tap", [])),
        top_sas=list(obj.get("top_sas", [])),
        lane_counts={k: int(v) for k, v in dict(obj.get("lane_counts", {})).items()},
        pfdi_alerts_count=int(obj.get("pfdi_alerts_count", 0)),
        pack_hash=obj.get("pack_hash"),
    )


def _state_from_dict(obj: Dict[str, Any]) -> ChronoscopeState:
    series = [_daypoint_from_dict(dp) for dp in obj.get("series", [])]
    return ChronoscopeState(
        version=int(obj.get("version", 1)),
        key_fingerprint=obj.get("key_fingerprint"),
        series=series,
    )


def load_state(path: Path) -> ChronoscopeState:
    if not path.exists():
        return ChronoscopeState(version=1, key_fingerprint=None, series=[])
    raw = json.loads(path.read_text(encoding="utf-8"))
    return _state_from_dict(raw)


def update_state(state: ChronoscopeState, day_point: DayPoint) -> ChronoscopeState:
    series = [dp for dp in state.series if dp.date != day_point.date]
    series.append(day_point)
    series_sorted = sorted(series, key=lambda dp: dp.date)
    return ChronoscopeState(version=state.version, key_fingerprint=state.key_fingerprint, series=series_sorted)


def write_state(path: Path, state: ChronoscopeState) -> None:
    payload = {
        "version": state.version,
        "key_fingerprint": state.key_fingerprint,
        "series": [asdict(dp) for dp in state.series],
    }
    path.write_text(stable_json_dumps(payload) + "\n", encoding="utf-8", newline="\n")
