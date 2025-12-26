from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple


def _parse_dt(s: str) -> Optional[datetime]:
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _read_jsonl(path: str, max_lines: int = 500000) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    out: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= max_lines:
                break
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if isinstance(obj, dict):
                out.append(obj)
    return out


def _window_velocity(obs: List[Tuple[datetime, int]], window_days: int, now: datetime) -> float:
    start = now - timedelta(days=window_days)
    total = 0
    for ts, count in obs:
        if ts >= start:
            total += int(count)
    return float(total) / float(max(1, window_days))


def _recurrence_days(obs_ts: List[datetime]) -> Optional[float]:
    if len(obs_ts) < 2:
        return None
    obs_ts = sorted(obs_ts)
    gaps = []
    for a, b in zip(obs_ts[:-1], obs_ts[1:]):
        gaps.append((b - a).total_seconds() / 86400.0)
    gaps = [g for g in gaps if g >= 0.0]
    if not gaps:
        return None
    gaps.sort()
    mid = len(gaps) // 2
    if len(gaps) % 2 == 1:
        return float(gaps[mid])
    return float((gaps[mid - 1] + gaps[mid]) / 2.0)


def _decay_fit_half_life_days(v14: float, v60: float) -> float:
    r = (v14 + 1e-6) / (v60 + 1e-6)
    if r < 1.0:
        hl = 14.0 * max(0.25, r)
    else:
        hl = 30.0 * min(3.0, r)
    return float(max(0.5, min(90.0, hl)))


def _phase_state(
    *,
    first_seen: datetime,
    last_seen: datetime,
    now: datetime,
    v14: float,
    v60: float,
    prev_gap_days: Optional[float],
) -> str:
    active = (now - last_seen).total_seconds() <= 7 * 86400
    dormant = (now - last_seen).total_seconds() >= 21 * 86400
    recent_first = (now - first_seen).total_seconds() <= 7 * 86400
    ratio = (v14 + 1e-6) / (v60 + 1e-6)

    if active and prev_gap_days is not None and prev_gap_days >= 14.0:
        return "resurgent"
    if dormant:
        return "dormant"
    if recent_first and v14 >= 0.8:
        return "emergent"
    if active and ratio >= 1.8 and v14 >= 0.6:
        return "surging"
    if active and 0.7 <= ratio <= 1.3:
        return "plateau"
    if active and ratio <= 0.6:
        return "decaying"
    return "plateau" if active else "decaying"


@dataclass(frozen=True)
class TermTemporalProfile:
    term_key: str
    term: str
    first_seen_ts: str
    last_seen_ts: str
    obs_n: int
    v14: float
    v60: float
    recurrence_days: Optional[float]
    half_life_days_fit: float
    phase: str
    manipulation_risk_mean: float
    novelty_mean: float
    propagation_mean: float
    tags_union: List[str]
    provenance: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def build_temporal_profiles(
    registry_path: str,
    *,
    now_iso: Optional[str] = None,
    max_terms: int = 2000,
    min_obs: int = 2,
) -> List[TermTemporalProfile]:
    now = _parse_dt(now_iso) if now_iso else None
    now = now or _utc_now()

    rows = _read_jsonl(registry_path)
    by_key: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        key = row.get("term_key")
        term = row.get("term")
        ts = (
            _parse_dt(str(row.get("ts") or ""))
            or _parse_dt(str(row.get("last_seen_ts") or ""))
            or None
        )
        if not key or not term or not ts:
            continue
        by_key.setdefault(str(key), []).append(row)

    profiles: List[TermTemporalProfile] = []
    for key, recs in by_key.items():
        obs: List[Tuple[datetime, int]] = []
        obs_ts: List[datetime] = []
        term = str(recs[-1].get("term") or "")
        tags_union = set()
        risk_vals = []
        nov_vals = []
        prop_vals = []

        first_seen = None
        last_seen = None

        for rec in recs:
            t_last = _parse_dt(str(rec.get("last_seen_ts") or "")) or _parse_dt(
                str(rec.get("ts") or "")
            )
            t_first = _parse_dt(str(rec.get("first_seen_ts") or "")) or t_last
            if not t_last:
                continue
            count = int(rec.get("count") or 0)
            obs.append((t_last, count))
            obs_ts.append(t_last)
            tags_union.update(list(rec.get("tags") or []))
            risk_vals.append(float(rec.get("manipulation_risk") or 0.0))
            nov_vals.append(float(rec.get("novelty_score") or 0.0))
            prop_vals.append(float(rec.get("propagation_score") or 0.0))

            if first_seen is None or (t_first and t_first < first_seen):
                first_seen = t_first
            if last_seen is None or t_last > last_seen:
                last_seen = t_last

        if not obs or not first_seen or not last_seen:
            continue
        if len(obs) < min_obs:
            continue

        v14 = _window_velocity(obs, 14, now)
        v60 = _window_velocity(obs, 60, now)
        rec_days = _recurrence_days(obs_ts)
        hl_fit = _decay_fit_half_life_days(v14, v60)
        phase = _phase_state(
            first_seen=first_seen,
            last_seen=last_seen,
            now=now,
            v14=v14,
            v60=v60,
            prev_gap_days=rec_days,
        )

        risk_mean = sum(risk_vals) / max(1, len(risk_vals))
        nov_mean = sum(nov_vals) / max(1, len(nov_vals))
        prop_mean = sum(prop_vals) / max(1, len(prop_vals))

        profiles.append(
            TermTemporalProfile(
                term_key=str(key),
                term=term,
                first_seen_ts=first_seen.isoformat(),
                last_seen_ts=last_seen.isoformat(),
                obs_n=len(obs),
                v14=float(v14),
                v60=float(v60),
                recurrence_days=rec_days,
                half_life_days_fit=float(hl_fit),
                phase=phase,
                manipulation_risk_mean=float(risk_mean),
                novelty_mean=float(nov_mean),
                propagation_mean=float(prop_mean),
                tags_union=sorted(list(tags_union)),
                provenance={
                    "method": "build_temporal_profiles.v0.1",
                    "registry": registry_path,
                },
            )
        )

    phase_rank = {
        "surging": 0,
        "resurgent": 1,
        "emergent": 2,
        "plateau": 3,
        "decaying": 4,
        "dormant": 5,
    }

    def score(p: TermTemporalProfile) -> Tuple[int, float, float, str]:
        pr = phase_rank.get(p.phase, 9)
        return (pr, -(p.v14 + 0.35 * p.v60), p.manipulation_risk_mean, p.term)

    profiles.sort(key=score)
    return profiles[:max_terms] if (max_terms is not None) else profiles
