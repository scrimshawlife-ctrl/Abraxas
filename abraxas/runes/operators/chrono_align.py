"""ABX-Rune Operator: RUNE.CHRONO_ALIGN (CHA).

Shadow-only window mapper. Pure and seedable.
Consumes CHRONO_SCAN observed metrics. Does not read wall clock,
invent windows, claim action success, or influence Forecast.
"""

from __future__ import annotations

from typing import Literal, Mapping, Sequence

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex

RUNE_ID = "RUNE.CHRONO_ALIGN"
RUNE_VERSION = "v0.1.0"
LANE: Literal["SHADOW"] = "SHADOW"
INFLUENCE_POLICY: Literal["NONE"] = "NONE"

_METRIC_KEYS = (
    "cadence_interval",
    "recurrence_strength",
    "window_density",
    "timing_volatility",
    "cadence_stability",
    "recurrence_pressure",
)
_INCOMING_FAIL_FLAGS = frozenset(
    {
        "NOT_COMPUTABLE",
        "timestamps_missing",
        "event_density_too_weak",
        "window_config_invalid",
        "metrics_not_computable",
    }
)

_MIN_RECURRENCE = 0.5
_MIN_STABILITY = 0.5
_MAX_VOLATILITY = 0.75
_DEFAULT_MIN_CONFIDENCE = 0.5

_FLAG_METRICS = "metrics_not_computable"
_FLAG_NO_WINDOW = "no_lawful_window"
_FLAG_POLICY = "policy_invalid"
_FLAG_NOT_COMPUTABLE = "NOT_COMPUTABLE"

_READINESS_SHADOW = "shadow_candidate"


class ChronoAlignInferred(BaseModel):
    alignment_window: str | None = None
    execution_readiness: str | None = None
    timing_advantage_hypothesis: str | None = None
    window_decay_rate: float | None = None
    not_computable_flags: list[str] = Field(default_factory=list)


class ChronoAlignProvenance(BaseModel):
    rune_id: str = RUNE_ID
    version: str = RUNE_VERSION
    run_id: str | None = None
    input_hash: str
    output_hash: str
    catalog_hash: str | None = None
    timestamp: str | None = None
    computation_path: list[str] = Field(default_factory=list)
    confidence: float | None = None


class ChronoAlignResult(BaseModel):
    rune_id: str = RUNE_ID
    lane: Literal["SHADOW"] = LANE
    influence_policy: Literal["NONE"] = INFLUENCE_POLICY
    inferred: ChronoAlignInferred
    provenance: ChronoAlignProvenance


def align(
    observed_temporal_metrics: object,
    *,
    candidate_actions: object = None,
    alignment_policy: object = None,
    seed: object = None,
    run_id: object = None,
    timestamp: object = None,
    catalog_hash: object = None,
    strict_execution: bool = False,
) -> ChronoAlignResult:
    """Map SCAN metrics to a bounded window. Never invent a window."""
    del strict_execution
    path = ["parse_inputs"]
    actions = _string_list(candidate_actions)
    caller_ts = _optional_string(timestamp)
    input_hash = _input_hash(
        observed_temporal_metrics,
        actions,
        alignment_policy,
        seed,
        run_id,
        caller_ts,
        catalog_hash,
    )

    metrics, metrics_ok = _parse_metrics(observed_temporal_metrics)
    if not metrics_ok:
        return _null_result(
            flags=[_FLAG_METRICS, _FLAG_NOT_COMPUTABLE],
            path=path + ["reject_metrics", "not_computable"],
            input_hash=input_hash,
            run_id=run_id,
            catalog_hash=catalog_hash,
            timestamp=caller_ts,
        )

    policy, policy_ok = _parse_policy(alignment_policy)
    if not policy_ok:
        return _null_result(
            flags=[_FLAG_POLICY, _FLAG_NOT_COMPUTABLE],
            path=path + ["reject_alignment_policy", "not_computable"],
            input_hash=input_hash,
            run_id=run_id,
            catalog_hash=catalog_hash,
            timestamp=caller_ts,
        )

    path.append("evaluate_lawful_window")
    incoming_flags = _incoming_flags(observed_temporal_metrics)
    if incoming_flags & _INCOMING_FAIL_FLAGS:
        return _null_result(
            flags=[_FLAG_METRICS, _FLAG_NOT_COMPUTABLE],
            path=path + ["incoming_not_computable"],
            input_hash=input_hash,
            run_id=run_id,
            catalog_hash=catalog_hash,
            timestamp=caller_ts,
        )

    if not _metrics_present(metrics):
        return _null_result(
            flags=[_FLAG_METRICS, _FLAG_NOT_COMPUTABLE],
            path=path + ["metrics_absent", "not_computable"],
            input_hash=input_hash,
            run_id=run_id,
            catalog_hash=catalog_hash,
            timestamp=caller_ts,
        )

    confidence = _alignment_confidence(metrics)
    path.append("score_confidence")
    if not _window_is_lawful(metrics, policy, confidence):
        return _null_result(
            flags=[_FLAG_NO_WINDOW, _FLAG_NOT_COMPUTABLE],
            path=path + ["no_lawful_window"],
            input_hash=input_hash,
            run_id=run_id,
            catalog_hash=catalog_hash,
            timestamp=caller_ts,
        )

    inferred = ChronoAlignInferred(
        alignment_window=_window_label(metrics["cadence_interval"], actions),
        execution_readiness=_READINESS_SHADOW,
        timing_advantage_hypothesis=_hypothesis(metrics["cadence_interval"]),
        window_decay_rate=_decay_rate(metrics),
    )
    path.append("emit_inferred_window")
    return _finalize(
        inferred,
        path=path,
        input_hash=input_hash,
        run_id=run_id,
        catalog_hash=catalog_hash,
        timestamp=caller_ts,
        confidence=confidence,
    )


def apply_chrono_align(
    observed_temporal_metrics: object = None,
    candidate_actions: object = None,
    alignment_policy: object = None,
    seed: object = None,
    run_id: object = None,
    timestamp: object = None,
    catalog_hash: object = None,
    *,
    strict_execution: bool = False,
    **_extra: object,
) -> dict[str, object]:
    """Registry/invoke adapter. Returns a dict; align() is the typed API."""
    result = align(
        observed_temporal_metrics,
        candidate_actions=candidate_actions,
        alignment_policy=alignment_policy,
        seed=seed,
        run_id=run_id,
        timestamp=timestamp,
        catalog_hash=catalog_hash,
        strict_execution=strict_execution,
    )
    return result.model_dump()


def _as_mapping(raw: object) -> Mapping[str, object] | None:
    if isinstance(raw, Mapping):
        return raw
    dumped = getattr(raw, "model_dump", None)
    if callable(dumped):
        payload = dumped()
        if isinstance(payload, Mapping):
            return payload
    return None


def _unwrap_metrics(raw: object) -> object:
    if raw is None:
        return None
    observed = getattr(raw, "observed", None)
    if observed is not None and not isinstance(raw, Mapping):
        return observed
    mapping = _as_mapping(raw)
    if mapping is None:
        return raw
    nested = mapping.get("observed")
    if _as_mapping(nested) is not None:
        return nested
    return mapping


def _finite_number(raw: object) -> float | None:
    if isinstance(raw, bool) or raw is None:
        return None
    if isinstance(raw, (int, float)):
        value = float(raw)
        if value != value or value in (float("inf"), float("-inf")):
            return None
        return value
    return None


def _optional_unit_interval(raw: object) -> tuple[float | None, bool]:
    if raw is None:
        return None, True
    value = _finite_number(raw)
    if value is None:
        return None, False
    if value < 0.0 or value > 1.0:
        return None, False
    return value, True


def _parse_metrics(raw: object) -> tuple[dict[str, float | None], bool]:
    empty = {key: None for key in _METRIC_KEYS}
    if raw is None:
        return empty, False
    payload = _unwrap_metrics(raw)
    mapping = _as_mapping(payload)
    if mapping is None:
        return empty, False
    parsed: dict[str, float | None] = {}
    for key in _METRIC_KEYS:
        if key not in mapping:
            parsed[key] = None
            continue
        value = mapping.get(key)
        if value is None:
            parsed[key] = None
            continue
        number = _finite_number(value)
        if number is None:
            return empty, False
        parsed[key] = number
    return parsed, True


def _incoming_flags(raw: object) -> set[str]:
    payload = _unwrap_metrics(raw)
    mapping = _as_mapping(payload)
    if mapping is None:
        return set()
    flags = mapping.get("not_computable_flags")
    if not isinstance(flags, Sequence) or isinstance(flags, (str, bytes, bytearray)):
        return set()
    return {item for item in flags if isinstance(item, str) and item}


def _parse_policy(raw: object) -> tuple[dict[str, float | None], bool]:
    empty: dict[str, float | None] = {"min_confidence": None, "max_window_span": None}
    if raw is None:
        return empty, True
    mapping = _as_mapping(raw)
    if mapping is None:
        return empty, False
    min_confidence, min_ok = _optional_unit_interval(mapping.get("min_confidence"))
    max_span, span_ok = _parse_span(mapping.get("max_window_span"))
    if not min_ok or not span_ok:
        return empty, False
    return {"min_confidence": min_confidence, "max_window_span": max_span}, True


def _parse_span(raw: object) -> tuple[float | None, bool]:
    if raw is None:
        return None, True
    if isinstance(raw, bool):
        return None, False
    if isinstance(raw, (int, float)):
        if raw != raw or raw <= 0:
            return None, False
        return float(raw), True
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
        return float(text) > 0
    except ValueError:
        return False


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


def _metrics_present(metrics: dict[str, float | None]) -> bool:
    interval = metrics["cadence_interval"]
    strength = metrics["recurrence_strength"]
    return interval is not None and interval > 0 and strength is not None


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _round(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 6)


def _alignment_confidence(metrics: dict[str, float | None]) -> float | None:
    strength = metrics["recurrence_strength"]
    stability = metrics["cadence_stability"]
    if strength is None or stability is None:
        return None
    volatility = metrics["timing_volatility"]
    if volatility is None:
        volatility = 1.0 - _clamp01(stability)
    pressure = metrics["recurrence_pressure"]
    pressure_term = 0.5 if pressure is None else 0.5 + 0.5 * _clamp01(pressure)
    raw = _clamp01(strength) * _clamp01(stability) * (1.0 - _clamp01(volatility)) * pressure_term
    return _round(raw)


def _window_is_lawful(
    metrics: dict[str, float | None],
    policy: dict[str, float | None],
    confidence: float | None,
) -> bool:
    interval = metrics["cadence_interval"]
    strength = metrics["recurrence_strength"]
    stability = metrics["cadence_stability"]
    volatility = metrics["timing_volatility"]
    if interval is None or interval <= 0:
        return False
    if strength is None or strength < _MIN_RECURRENCE:
        return False
    if stability is None or stability < _MIN_STABILITY:
        return False
    if volatility is not None and volatility > _MAX_VOLATILITY:
        return False
    if confidence is None:
        return False
    min_confidence = policy["min_confidence"]
    floor = _DEFAULT_MIN_CONFIDENCE if min_confidence is None else min_confidence
    if confidence < floor:
        return False
    max_span = policy["max_window_span"]
    if max_span is not None and interval > max_span:
        return False
    return True


def _format_interval(interval: float) -> str:
    if interval == int(interval):
        return str(int(interval))
    return f"{_round(interval)}"


def _window_label(interval: float | None, actions: list[str]) -> str:
    assert interval is not None
    label = f"next_cycle[{_format_interval(interval)}s]"
    if actions:
        joined = "|".join(actions)
        label = f"{label};candidates={joined}"
    return label


def _hypothesis(interval: float | None) -> str:
    assert interval is not None
    return (
        f"bounded next-cycle[{_format_interval(interval)}s]; "
        "shadow-only; no outcome certainty"
    )


def _decay_rate(metrics: dict[str, float | None]) -> float | None:
    volatility = metrics["timing_volatility"]
    if volatility is not None:
        return _round(_clamp01(volatility))
    stability = metrics["cadence_stability"]
    if stability is None:
        return None
    return _round(1.0 - _clamp01(stability))


def _unique_flags(flags: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for flag in flags:
        if flag not in seen:
            seen.add(flag)
            out.append(flag)
    return out


def _canonical_metrics(raw: object) -> object:
    payload = _unwrap_metrics(raw)
    mapping = _as_mapping(payload)
    if mapping is None:
        return None
    return {key: mapping.get(key) for key in (*_METRIC_KEYS, "not_computable_flags")}


def _input_hash(
    metrics: object,
    actions: list[str],
    alignment_policy: object,
    seed: object,
    run_id: object,
    timestamp: str | None,
    catalog_hash: object,
) -> str:
    payload = {
        "alignment_policy": alignment_policy if isinstance(alignment_policy, Mapping) else None,
        "candidate_actions": actions,
        "catalog_hash": catalog_hash if isinstance(catalog_hash, str) else None,
        "observed_temporal_metrics": _canonical_metrics(metrics),
        "run_id": run_id if isinstance(run_id, str) else None,
        "seed": seed if isinstance(seed, (int, str)) and not isinstance(seed, bool) else None,
        "timestamp": timestamp,
    }
    return sha256_hex(canonical_json(payload))


def _null_result(
    *,
    flags: list[str],
    path: list[str],
    input_hash: str,
    run_id: object,
    catalog_hash: object,
    timestamp: str | None,
) -> ChronoAlignResult:
    inferred = ChronoAlignInferred(not_computable_flags=_unique_flags(flags))
    return _finalize(
        inferred,
        path=path,
        input_hash=input_hash,
        run_id=run_id,
        catalog_hash=catalog_hash,
        timestamp=timestamp,
        confidence=None,
    )


def _finalize(
    inferred: ChronoAlignInferred,
    *,
    path: list[str],
    input_hash: str,
    run_id: object,
    catalog_hash: object,
    timestamp: str | None,
    confidence: float | None,
) -> ChronoAlignResult:
    output_hash = sha256_hex(canonical_json(inferred.model_dump()))
    provenance = ChronoAlignProvenance(
        run_id=run_id if isinstance(run_id, str) else None,
        input_hash=input_hash,
        output_hash=output_hash,
        catalog_hash=catalog_hash if isinstance(catalog_hash, str) else None,
        timestamp=timestamp,
        computation_path=list(path),
        confidence=_round(confidence),
    )
    return ChronoAlignResult(inferred=inferred, provenance=provenance)
