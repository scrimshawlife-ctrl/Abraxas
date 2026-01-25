from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Tuple

from .scoring import stable_round


@dataclass(frozen=True)
class WatchlistRule:
    id: str
    label: str
    kind: str  # token|subword
    target: str
    metric: str  # sas|tap|pfdi
    trigger_delta: float
    trigger_score: float
    decay_halflife_days: int
    min_days_seen: int


@dataclass(frozen=True)
class WatchlistState:
    last_triggered_by_id: Dict[str, str]
    decay_state: Dict[str, float]
    history: List[Dict[str, Any]]


def default_state() -> WatchlistState:
    return WatchlistState(last_triggered_by_id={}, decay_state={}, history=[])


def _parse_date(s: str) -> date | None:
    try:
        parts = [int(p) for p in str(s).split("-")]
        if len(parts) != 3:
            return None
        return date(parts[0], parts[1], parts[2])
    except ValueError:
        return None


def _decay_value(value: float, days: int, halflife: int) -> float:
    if halflife <= 0:
        return 0.0
    return value * (0.5 ** (days / float(halflife)))


def _extract_metric(day_point: Dict[str, Any], rule: WatchlistRule) -> float | None:
    if rule.metric == "pfdi":
        return float(day_point.get("pfdi_alerts_count", 0))
    if rule.metric == "tap":
        for row in day_point.get("top_tap", []):
            if row.get("token") == rule.target:
                return float(row.get("tap", 0.0))
        return None
    if rule.metric == "sas":
        for row in day_point.get("top_sas", []):
            if row.get("sub") == rule.target:
                return float(row.get("sas", 0.0))
        return None
    return None


def _baseline(history: List[Dict[str, Any]], rule: WatchlistRule) -> float:
    values = []
    for dp in history:
        v = _extract_metric(dp, rule)
        if v is not None:
            values.append(v)
    if not values:
        return 0.0
    return sum(values) / len(values)


def _days_seen(history: List[Dict[str, Any]], rule: WatchlistRule) -> int:
    count = 0
    for dp in history:
        v = _extract_metric(dp, rule)
        if v is not None:
            count += 1
    return count


def evaluate_watchlist(
    day_point: Dict[str, Any],
    history: List[Dict[str, Any]],
    rules: List[WatchlistRule],
    state: WatchlistState,
) -> Tuple[List[Dict[str, Any]], WatchlistState]:
    triggers = []
    last_triggered = dict(state.last_triggered_by_id)
    decay_state = dict(state.decay_state)
    history_out = list(state.history)

    for rule in sorted(rules, key=lambda r: r.id):
        value = _extract_metric(day_point, rule)
        if value is None:
            continue
        baseline = _baseline(history, rule)
        delta = value - baseline
        score = delta / rule.trigger_delta if rule.trigger_delta != 0 else delta
        days_seen = _days_seen(history + [day_point], rule)
        if days_seen < rule.min_days_seen:
            continue

        last_date = last_triggered.get(rule.id)
        decay_prev = decay_state.get(rule.id, 0.0)
        decay_days = 0
        if last_date:
            last_dt = _parse_date(last_date)
            cur_dt = _parse_date(str(day_point.get("date")))
            if last_dt and cur_dt:
                decay_days = max(0, (cur_dt - last_dt).days)
            else:
                decay_days = 1
        decayed = _decay_value(decay_prev, decay_days, rule.decay_halflife_days)
        should_trigger = delta >= rule.trigger_delta and score >= rule.trigger_score and decayed <= 0.5

        if should_trigger:
            last_triggered[rule.id] = str(day_point.get("date"))
            decay_state[rule.id] = 1.0
            triggers.append({
                "id": rule.id,
                "label": rule.label,
                "target": rule.target,
                "metric": rule.metric,
                "date": day_point.get("date"),
                "value": stable_round(value),
                "baseline": stable_round(baseline),
                "delta": stable_round(delta),
                "score": stable_round(score),
            })
        else:
            decay_state[rule.id] = decayed

    history_out.append({"date": day_point.get("date"), "triggers": triggers})
    new_state = WatchlistState(last_triggered_by_id=last_triggered, decay_state=decay_state, history=history_out)
    return triggers, new_state
