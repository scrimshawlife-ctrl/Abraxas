"""ABX-Rune Operator: RUNE.CHRONO_SCAN (CHS).

Shadow-only timing-structure observer. Pure and seedable.
Does not read wall clock, invent cadence, or influence Forecast.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Literal, Mapping, Sequence

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex

RUNE_ID = "RUNE.CHRONO_SCAN"
RUNE_VERSION = "v0.1.0"
LANE: Literal["SHADOW"] = "SHADOW"
INFLUENCE_POLICY: Literal["NONE"] = "NONE"

_MIN_EVENTS = 3
_MIN_INTERVALS = 2
_MAX_CV_FOR_CADENCE = 0.75
_RECURRENCE_BAND = 0.15
_DEFAULT_TIME_FIELDS = ("timestamp", "ts", "t", "time", "observed_at", "event_time")

_FLAG_TIMESTAMPS_MISSING = "timestamps_missing"
_FLAG_DENSITY_WEAK = "event_density_too_weak"
_FLAG_WINDOW_INVALID = "window_config_invalid"
_FLAG_SOURCE_FAMILY_MISSING = "source_family_missing"
_FLAG_NOT_COMPUTABLE = "NOT_COMPUTABLE"
_MAX_EPOCH_SECONDS = 253402300799.0
_JSONABLE_DEPTH = 32


class ChronoScanObserved(BaseModel):
    cadence_interval: float | None = None
    recurrence_strength: float | None = None
    window_density: float | None = None
    timing_volatility: float | None = None
    cadence_stability: float | None = None
    recurrence_pressure: float | None = None
    not_computable_flags: list[str] = Field(default_factory=list)


class ChronoScanProvenance(BaseModel):
    rune_id: str = RUNE_ID
    version: str = RUNE_VERSION
    run_id: str | None = None
    input_hash: str
    output_hash: str
    catalog_hash: str | None = None
    timestamp: str | None = None
    computation_path: list[str] = Field(default_factory=list)
    source_family_trace: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
    confidence: float | None = None


class ChronoScanResult(BaseModel):
    rune_id: str = RUNE_ID
    lane: Literal["SHADOW"] = LANE
    influence_policy: Literal["NONE"] = INFLUENCE_POLICY
    observed: ChronoScanObserved
    provenance: ChronoScanProvenance


def scan(
    events: object,
    *,
    source_family: object = None,
    source_ids: object = None,
    time_field: object = None,
    window_config: object = None,
    seed: object = None,
    run_id: object = None,
    timestamp: object = None,
    catalog_hash: object = None,
    strict_execution: bool = False,
) -> ChronoScanResult:
    """Observe cadence/recurrence/clustering. Never invent structure."""
    path = ["parse_inputs"]
    families = _string_list(source_family)
    ids = _string_list(source_ids)
    field = _optional_string(time_field)
    caller_ts = _optional_string(timestamp)
    input_hash = _input_hash(
        events, families, ids, field, window_config, seed, run_id, caller_ts, catalog_hash
    )

    if not families:
        return _null_result(
            flags=[_FLAG_SOURCE_FAMILY_MISSING, _FLAG_NOT_COMPUTABLE],
            path=path + ["reject_source_family", "not_computable"],
            input_hash=input_hash,
            families=families,
            ids=ids,
            run_id=run_id,
            catalog_hash=catalog_hash,
            timestamp=caller_ts,
        )

    parsed = _as_event_list(events)
    if parsed is None:
        return _null_result(
            flags=[_FLAG_TIMESTAMPS_MISSING, _FLAG_NOT_COMPUTABLE],
            path=path + ["reject_events", "not_computable"],
            input_hash=input_hash,
            families=families,
            ids=ids,
            run_id=run_id,
            catalog_hash=catalog_hash,
            timestamp=caller_ts,
        )

    window, window_ok = _parse_window_config(window_config)
    if not window_ok:
        return _null_result(
            flags=[_FLAG_WINDOW_INVALID, _FLAG_NOT_COMPUTABLE],
            path=path + ["reject_window_config", "not_computable"],
            input_hash=input_hash,
            families=families,
            ids=ids,
            run_id=run_id,
            catalog_hash=catalog_hash,
            timestamp=caller_ts,
        )

    stamped, missing_timestamps = _extract_timestamps(parsed, field)
    path.append("extract_timestamps")
    if missing_timestamps or not stamped:
        return _null_result(
            flags=[_FLAG_TIMESTAMPS_MISSING, _FLAG_NOT_COMPUTABLE],
            path=path + ["reject_timestamps", "not_computable"],
            input_hash=input_hash,
            families=families,
            ids=ids,
            run_id=run_id,
            catalog_hash=catalog_hash,
            timestamp=caller_ts,
        )

    stamped.sort(key=lambda item: (item[0], item[1]))
    path.append("order_by_time")
    if window["lookback_span"] is not None:
        stamped = _apply_lookback(stamped, window["lookback_span"])
        path.append("apply_lookback")

    epochs = [item[0] for item in stamped]
    observed_ts = caller_ts or stamped[-1][2]
    if len(epochs) < _MIN_EVENTS:
        return _null_result(
            flags=[_FLAG_DENSITY_WEAK, _FLAG_NOT_COMPUTABLE],
            path=path + ["not_computable"],
            input_hash=input_hash,
            families=families,
            ids=ids,
            run_id=run_id,
            catalog_hash=catalog_hash,
            timestamp=observed_ts,
        )

    intervals = _intervals(epochs)
    path.append("compute_intervals")
    observed = _observed_metrics(epochs, intervals, window["bucket_size"])
    path.append("observed_metrics")
    return _finalize(
        observed,
        path=path,
        input_hash=input_hash,
        families=families,
        ids=ids,
        run_id=run_id,
        catalog_hash=catalog_hash,
        timestamp=observed_ts,
        interval_count=len(intervals),
    )


def apply_chrono_scan(
    events: object = None,
    source_family: object = None,
    source_ids: object = None,
    time_field: object = None,
    window_config: object = None,
    seed: object = None,
    run_id: object = None,
    timestamp: object = None,
    catalog_hash: object = None,
    *,
    strict_execution: bool = False,
    **_extra: object,
) -> dict[str, object]:
    """Registry/invoke adapter. Returns a dict; scan() is the typed API."""
    result = scan(
        events,
        source_family=source_family,
        source_ids=source_ids,
        time_field=time_field,
        window_config=window_config,
        seed=seed,
        run_id=run_id,
        timestamp=timestamp,
        catalog_hash=catalog_hash,
        strict_execution=strict_execution,
    )
    return result.model_dump()


def _as_event_list(raw: object) -> list[object] | None:
    if raw is None or isinstance(raw, (str, bytes, bytearray)):
        return None
    if isinstance(raw, Sequence):
        return list(raw)
    return None


def _string_list(raw: object) -> list[str]:
    if raw is None or isinstance(raw, (str, bytes, bytearray)):
        return []
    if not isinstance(raw, Sequence):
        return []
    out: list[str] = []
    for item in raw:
        if isinstance(item, str) and item:
            out.append(item)
    return out


def _optional_string(raw: object) -> str | None:
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return None


def _as_mapping(raw: object) -> Mapping[str, object] | None:
    if isinstance(raw, Mapping):
        return raw
    return None


def _parse_window_config(raw: object) -> tuple[dict[str, float | None], bool]:
    empty: dict[str, float | None] = {"lookback_span": None, "bucket_size": None}
    if raw is None:
        return empty, True
    mapping = _as_mapping(raw)
    if mapping is None:
        return empty, False
    lookback, lookback_ok = _parse_span(mapping.get("lookback_span"))
    bucket, bucket_ok = _parse_span(mapping.get("bucket_size"))
    if not lookback_ok or not bucket_ok:
        return empty, False
    return {"lookback_span": lookback, "bucket_size": bucket}, True


def _parse_span(raw: object) -> tuple[float | None, bool]:
    if raw is None:
        return None, True
    if isinstance(raw, bool):
        return None, False
    if isinstance(raw, (int, float)):
        value = float(raw)
        if not math.isfinite(value) or value <= 0:
            return None, False
        return value, True
    if not isinstance(raw, str):
        return None, False
    text = raw.strip().lower()
    if not text:
        return None, True
    units = {"s": 1.0, "m": 60.0, "h": 3600.0, "d": 86400.0}
    if text[-1] in units and _is_positive_number(text[:-1]):
        return float(text[:-1]) * units[text[-1]], True
    if _is_positive_number(text):
        return float(text), True
    return None, False


def _is_positive_number(text: str) -> bool:
    try:
        value = float(text)
    except ValueError:
        return False
    return math.isfinite(value) and value > 0


def _finite_epoch(value: float) -> float | None:
    if not math.isfinite(value) or value < 0:
        return None
    if value > 1e12:
        value = value / 1000.0
    if not math.isfinite(value) or value > _MAX_EPOCH_SECONDS:
        return None
    return value


def _epoch_seconds(raw: object) -> float | None:
    if isinstance(raw, bool) or raw is None:
        return None
    if isinstance(raw, (int, float)):
        return _finite_epoch(float(raw))
    if not isinstance(raw, str) or not raw.strip():
        return None
    text = raw.strip()
    try:
        numeric = float(text)
    except ValueError:
        return _iso_to_epoch(text)
    return _finite_epoch(numeric)


def _iso_to_epoch(text: str) -> float | None:
    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.timestamp()


def _extract_timestamps(
    events: list[object], time_field: str | None
) -> tuple[list[tuple[float, int, str]], int]:
    keys = (time_field,) if time_field else _DEFAULT_TIME_FIELDS
    stamped: list[tuple[float, int, str]] = []
    missing = 0
    for index, event in enumerate(events):
        mapping = _as_mapping(event)
        if mapping is None:
            missing += 1
            continue
        raw = None
        for key in keys:
            if key is None:
                continue
            if key in mapping:
                raw = mapping[key]
                break
        epoch = _epoch_seconds(raw)
        if epoch is None:
            missing += 1
            continue
        label = raw if isinstance(raw, str) else _epoch_to_iso(epoch)
        if not isinstance(label, str):
            missing += 1
            continue
        stamped.append((epoch, index, label))
    return stamped, missing


def _epoch_to_iso(epoch: float) -> str | None:
    try:
        return datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except (OverflowError, OSError, ValueError):
        return None


def _apply_lookback(
    stamped: list[tuple[float, int, str]], lookback: float
) -> list[tuple[float, int, str]]:
    latest = stamped[-1][0]
    floor = latest - lookback
    return [item for item in stamped if item[0] >= floor]


def _intervals(epochs: list[float]) -> list[float]:
    return [later - earlier for earlier, later in zip(epochs, epochs[1:])]


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / float(len(values))


def _pstdev(values: list[float]) -> float | None:
    mean = _mean(values)
    if mean is None or len(values) < 2:
        return None
    variance = sum((item - mean) ** 2 for item in values) / float(len(values))
    return math.sqrt(variance)


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def _round(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 6)


def _observed_metrics(
    epochs: list[float], intervals: list[float], bucket_size: float | None
) -> ChronoScanObserved:
    flags: list[str] = []
    cv: float | None = None
    mean_interval = _mean(intervals)
    stdev = _pstdev(intervals)
    if mean_interval is not None and mean_interval > 0 and stdev is not None:
        cv = stdev / mean_interval

    cadence_interval = None
    recurrence_strength = None
    recurrence_pressure = None
    if (
        len(intervals) >= _MIN_INTERVALS
        and cv is not None
        and cv <= _MAX_CV_FOR_CADENCE
    ):
        cadence_interval = _median(intervals)
        recurrence_strength = max(0.0, 1.0 - cv)
        if len(intervals) >= 3 and cadence_interval and cadence_interval > 0:
            band = cadence_interval * _RECURRENCE_BAND
            hits = sum(1 for item in intervals if abs(item - cadence_interval) <= band)
            recurrence_pressure = hits / float(len(intervals))
    elif len(intervals) >= _MIN_INTERVALS:
        flags.extend([_FLAG_DENSITY_WEAK, _FLAG_NOT_COMPUTABLE])
    else:
        flags.extend([_FLAG_DENSITY_WEAK, _FLAG_NOT_COMPUTABLE])

    span = epochs[-1] - epochs[0] if len(epochs) >= 2 else 0.0
    window_density = None
    if span > 0:
        if bucket_size is not None and bucket_size > 0:
            buckets = max(1.0, math.ceil(span / bucket_size))
            window_density = len(epochs) / buckets
        else:
            window_density = len(epochs) / span

    volatility = cv
    stability = None if cv is None else max(0.0, 1.0 - min(cv, 1.0))
    if flags:
        cadence_interval = None
        recurrence_strength = None
        recurrence_pressure = None

    return ChronoScanObserved(
        cadence_interval=_round(cadence_interval),
        recurrence_strength=_round(recurrence_strength),
        window_density=_round(window_density),
        timing_volatility=_round(volatility),
        cadence_stability=_round(stability),
        recurrence_pressure=_round(recurrence_pressure),
        not_computable_flags=_unique_flags(flags),
    )


def _unique_flags(flags: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for flag in flags:
        if flag not in seen:
            seen.add(flag)
            out.append(flag)
    return out


def _confidence(observed: ChronoScanObserved, interval_count: int) -> float | None:
    if observed.not_computable_flags:
        return None
    if observed.cadence_interval is None or observed.recurrence_strength is None:
        return None
    volume = min(1.0, interval_count / 8.0)
    return _round(volume * observed.recurrence_strength)


def _jsonable(value: object, *, depth: int = 0) -> object:
    if depth > _JSONABLE_DEPTH:
        return {"_truncated": True}
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        if math.isfinite(value):
            return value
        return {"_nonfinite": str(value)}
    if isinstance(value, Mapping):
        return {
            str(key): _jsonable(item, depth=depth + 1)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (bytes, bytearray)):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, Sequence):
        return [_jsonable(item, depth=depth + 1) for item in value]
    return {"_unserializable": type(value).__name__}


def _input_hash(
    events: object,
    families: list[str],
    ids: list[str],
    time_field: str | None,
    window_config: object,
    seed: object,
    run_id: object,
    timestamp: str | None,
    catalog_hash: object,
) -> str:
    if isinstance(events, Sequence) and not isinstance(events, (str, bytes, bytearray)):
        hashed_events: object = _jsonable(list(events))
    else:
        hashed_events = None
    payload = {
        "catalog_hash": catalog_hash if isinstance(catalog_hash, str) else None,
        "events": hashed_events,
        "run_id": run_id if isinstance(run_id, str) else None,
        "seed": seed if isinstance(seed, (int, str)) and not isinstance(seed, bool) else None,
        "source_family": families,
        "source_ids": ids,
        "time_field": time_field,
        "timestamp": timestamp,
        "window_config": _jsonable(window_config) if isinstance(window_config, Mapping) else None,
    }
    try:
        return sha256_hex(canonical_json(payload))
    except (TypeError, ValueError):
        fallback = {
            "catalog_hash": None,
            "events": {"_unserializable": type(events).__name__},
            "run_id": None,
            "seed": None,
            "source_family": list(families),
            "source_ids": list(ids),
            "time_field": time_field,
            "timestamp": timestamp,
            "window_config": None,
        }
        return sha256_hex(canonical_json(fallback))


def _null_result(
    *,
    flags: list[str],
    path: list[str],
    input_hash: str,
    families: list[str],
    ids: list[str],
    run_id: object,
    catalog_hash: object,
    timestamp: str | None,
) -> ChronoScanResult:
    observed = ChronoScanObserved(not_computable_flags=_unique_flags(flags))
    return _finalize(
        observed,
        path=path,
        input_hash=input_hash,
        families=families,
        ids=ids,
        run_id=run_id,
        catalog_hash=catalog_hash,
        timestamp=timestamp,
        interval_count=0,
    )


def _finalize(
    observed: ChronoScanObserved,
    *,
    path: list[str],
    input_hash: str,
    families: list[str],
    ids: list[str],
    run_id: object,
    catalog_hash: object,
    timestamp: str | None,
    interval_count: int,
) -> ChronoScanResult:
    output_hash = sha256_hex(canonical_json(observed.model_dump()))
    provenance = ChronoScanProvenance(
        run_id=run_id if isinstance(run_id, str) else None,
        input_hash=input_hash,
        output_hash=output_hash,
        catalog_hash=catalog_hash if isinstance(catalog_hash, str) else None,
        timestamp=timestamp,
        computation_path=list(path),
        source_family_trace=list(families),
        source_ids=list(ids),
        confidence=_confidence(observed, interval_count),
    )
    return ChronoScanResult(observed=observed, provenance=provenance)
