"""ABX-Rune Operator: RUNE.CALIBRATION (CAL).

Shadow typed stub only. Placeholder types stay NOT_COMPUTABLE.
Does not implement FORECAST_SCORE, activate live Forecast scoring,
invent calibration incidents, or mutate Forecast weights.
"""

from __future__ import annotations

from typing import Literal, Mapping, Sequence

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex

RUNE_ID = "RUNE.CALIBRATION"
RUNE_VERSION = "v0.1.0"
LANE: Literal["SHADOW"] = "SHADOW"
INFLUENCE_POLICY: Literal["NONE"] = "NONE"
CATEGORY: Literal["VALIDATE"] = "VALIDATE"
DECLARED_DEPENDENCIES = (
    "RUNE.FORECAST_SCORE",
    "RUNE.CONTINUITY",
    "RUNE.ERS",
)

_FLAG_NOT_COMPUTABLE = "NOT_COMPUTABLE"
_FLAG_METRIC = "metric_not_computable"
_FLAG_MISSING_RESOLUTION = "missing_resolution_data"
_FLAG_HORIZON_MISMATCH = "horizon_mismatch"
_FLAG_WEAK = "placeholder_or_weak_input"

_IDENTIFYING_KEYS = (
    "id",
    "lifecycle_id",
    "lifecycleId",
    "score_id",
    "scoreId",
    "horizon_id",
    "horizonId",
)
_HORIZON_KEYS = ("horizon", "horizon_id", "horizonId", "band", "horizon_band")
_RESOLUTION_KEYS = (
    "resolution",
    "resolved",
    "outcome",
    "resolved_at",
    "resolvedAt",
    "resolution_id",
    "resolutionId",
    "actual",
)


class ForecastLifecycleStub(BaseModel):
    """Placeholder ForecastLifecycle. NOT_COMPUTABLE. Not a Forecast engine."""

    type_name: Literal["ForecastLifecycle"] = "ForecastLifecycle"
    status: Literal["NOT_COMPUTABLE"] = "NOT_COMPUTABLE"
    lifecycle_id: str | None = None
    horizon: str | None = None
    score: None = None


class ForecastScoreStub(BaseModel):
    """Placeholder ForecastScore. NOT_COMPUTABLE. Not a live score."""

    type_name: Literal["ForecastScore"] = "ForecastScore"
    status: Literal["NOT_COMPUTABLE"] = "NOT_COMPUTABLE"
    score_id: str | None = None
    horizon: str | None = None
    value: None = None


class HorizonSpecStub(BaseModel):
    """Placeholder HorizonSpec. NOT_COMPUTABLE. Not a runtime horizon."""

    type_name: Literal["HorizonSpec"] = "HorizonSpec"
    status: Literal["NOT_COMPUTABLE"] = "NOT_COMPUTABLE"
    spec_id: str | None = None
    horizon: str | None = None


class CalibrationReportStub(BaseModel):
    """Placeholder CalibrationReport. NOT_COMPUTABLE. Not a live report."""

    type_name: Literal["CalibrationReport"] = "CalibrationReport"
    status: Literal["NOT_COMPUTABLE"] = "NOT_COMPUTABLE"
    report_id: None = None
    incidents: None = None
    score: None = None
    live_scoring_activated: Literal[False] = False


class PerformanceDriftStub(BaseModel):
    """Placeholder PerformanceDrift. NOT_COMPUTABLE. Not a drift engine."""

    type_name: Literal["PerformanceDrift"] = "PerformanceDrift"
    status: Literal["NOT_COMPUTABLE"] = "NOT_COMPUTABLE"
    magnitude: None = None
    direction: None = None


class HorizonMetricsStub(BaseModel):
    """Placeholder HorizonMetrics. NOT_COMPUTABLE. Not a scoring surface."""

    type_name: Literal["HorizonMetrics"] = "HorizonMetrics"
    status: Literal["NOT_COMPUTABLE"] = "NOT_COMPUTABLE"
    coverage: None = None
    score: None = None


class CalibrationMetricsView(BaseModel):
    """Metrics derived only from emitted artifacts. Same artifacts → same view."""

    status: Literal["NOT_COMPUTABLE"] = "NOT_COMPUTABLE"
    metric_not_computable: Literal[True] = True
    calibration_score: None = None
    drift_magnitude: None = None
    horizon_coverage: None = None
    artifacts_hash: str
    live_scoring_activated: Literal[False] = False
    incidents: None = None


class CalibrationProvenance(BaseModel):
    rune_id: str = RUNE_ID
    version: str = RUNE_VERSION
    run_id: str | None = None
    input_hash: str
    output_hash: str
    catalog_hash: str | None = None
    timestamp: str | None = None
    computation_path: list[str] = Field(default_factory=list)
    confidence: None = None


class CalibrationResult(BaseModel):
    rune_id: str = RUNE_ID
    lane: Literal["SHADOW"] = LANE
    influence_policy: Literal["NONE"] = INFLUENCE_POLICY
    category: Literal["VALIDATE"] = CATEGORY
    calibration_report: CalibrationReportStub | None
    performance_drift: PerformanceDriftStub | None
    horizon_metrics: HorizonMetricsStub | None
    calibration_incidents: None = None
    live_scoring_activated: Literal[False] = False
    forecast_mutation: None = None
    forecast_weights: None = None
    not_computable_flags: list[str] = Field(default_factory=list)
    provenance: CalibrationProvenance


def calibrate(
    forecast_lifecycles: object,
    forecast_scores: object,
    horizon_spec: object,
    *,
    seed: object = None,
    run_id: object = None,
    timestamp: object = None,
    catalog_hash: object = None,
    strict_execution: bool = False,
) -> CalibrationResult:
    """Accept forecastLifecycles + forecastScores + horizonSpec. Never score live."""
    del strict_execution
    path = ["parse_inputs"]
    caller_ts = _optional_string(timestamp)
    input_hash = _input_hash(
        forecast_lifecycles,
        forecast_scores,
        horizon_spec,
        seed,
        run_id,
        caller_ts,
        catalog_hash,
    )

    cycles, cycles_ok, cycles_weak = _parse_lifecycle_list(forecast_lifecycles)
    scores, scores_ok, scores_weak = _parse_score_list(forecast_scores)
    spec, spec_ok, spec_weak = _parse_horizon_spec(horizon_spec)

    if not cycles_ok or not scores_ok or not spec_ok:
        path.extend(["reject_schema", "not_computable"])
        return _null_result(
            flags=[
                _FLAG_NOT_COMPUTABLE,
                _FLAG_METRIC,
                _FLAG_MISSING_RESOLUTION,
                _FLAG_WEAK,
            ],
            path=path,
            input_hash=input_hash,
            run_id=run_id,
            catalog_hash=catalog_hash,
            timestamp=caller_ts,
        )

    path.append("typed_stub")
    flags = [_FLAG_NOT_COMPUTABLE, _FLAG_METRIC]
    missing_resolution = (
        cycles is None
        or scores is None
        or not cycles
        or not scores
        or not _has_resolution_data(forecast_lifecycles, forecast_scores)
    )
    if missing_resolution:
        flags.append(_FLAG_MISSING_RESOLUTION)
        path.append("missing_resolution_data")
    horizon_mismatch = _horizons_mismatch(cycles, scores, spec, horizon_spec)
    if horizon_mismatch:
        flags.append(_FLAG_HORIZON_MISMATCH)
        path.append("horizon_mismatch")
    if cycles_weak or scores_weak or spec_weak or spec is None:
        flags.append(_FLAG_WEAK)
        path.append("weak_or_placeholder")
    path.append("not_computable")

    emit_placeholders = (
        not missing_resolution
        and not horizon_mismatch
        and spec is not None
        and not cycles_weak
        and not scores_weak
        and not spec_weak
    )
    del cycles, scores, spec
    if emit_placeholders:
        return _placeholder_result(
            flags=flags,
            path=path,
            input_hash=input_hash,
            run_id=run_id,
            catalog_hash=catalog_hash,
            timestamp=caller_ts,
        )
    return _null_result(
        flags=flags,
        path=path,
        input_hash=input_hash,
        run_id=run_id,
        catalog_hash=catalog_hash,
        timestamp=caller_ts,
    )


def apply_calibration(
    forecastLifecycles: object = None,
    forecastScores: object = None,
    horizonSpec: object = None,
    seed: object = None,
    run_id: object = None,
    timestamp: object = None,
    catalog_hash: object = None,
    *,
    forecast_lifecycles: object = None,
    forecast_scores: object = None,
    horizon_spec: object = None,
    strict_execution: bool = False,
    **_extra: object,
) -> dict[str, object]:
    """Registry/invoke adapter. Returns a dict; calibrate() is the typed API."""
    result = calibrate(
        forecastLifecycles if forecastLifecycles is not None else forecast_lifecycles,
        forecastScores if forecastScores is not None else forecast_scores,
        horizonSpec if horizonSpec is not None else horizon_spec,
        seed=seed,
        run_id=run_id,
        timestamp=timestamp,
        catalog_hash=catalog_hash,
        strict_execution=strict_execution,
    )
    return result.model_dump()


def metrics_from_emitted_artifacts(
    calibration_report: object,
    performance_drift: object,
    horizon_metrics: object,
) -> CalibrationMetricsView:
    """Recompute metrics from emitted artifacts only. Same artifacts → same metrics."""
    payload = {
        "calibration_report": _canonical_mapping(calibration_report),
        "horizon_metrics": _canonical_mapping(horizon_metrics),
        "performance_drift": _canonical_mapping(performance_drift),
    }
    return CalibrationMetricsView(artifacts_hash=sha256_hex(canonical_json(payload)))


def activates_live_forecast_scoring() -> bool:
    """Typed stub never activates live Forecast scoring."""
    return False


def implements_forecast_score() -> bool:
    """Declared dep only. FORECAST_SCORE is not implemented here."""
    return False


def _as_mapping(raw: object) -> Mapping[str, object] | None:
    if isinstance(raw, Mapping):
        return raw
    dumped = getattr(raw, "model_dump", None)
    if callable(dumped):
        payload = dumped()
        if isinstance(payload, Mapping):
            return payload
    return None


def _as_sequence(raw: object) -> list[object] | None:
    if raw is None or isinstance(raw, (str, bytes, bytearray)):
        return None
    if isinstance(raw, Sequence):
        return list(raw)
    return None


def _optional_string(raw: object) -> str | None:
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return None


def _echo_id(mapping: Mapping[str, object]) -> str | None:
    for key in _IDENTIFYING_KEYS:
        value = mapping.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _echo_horizon(mapping: Mapping[str, object] | None) -> str | None:
    if mapping is None:
        return None
    for key in _HORIZON_KEYS:
        value = mapping.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _is_placeholder_mapping(mapping: Mapping[str, object]) -> bool:
    status = mapping.get("status")
    if status in {_FLAG_NOT_COMPUTABLE, "not_computable"}:
        return True
    if mapping.get("placeholder") is True:
        return True
    if _echo_id(mapping) is None and not any(
        key not in {"type", "type_name", "status", "placeholder"} for key in mapping
    ):
        return True
    return False


def _parse_lifecycle_list(
    raw: object,
) -> tuple[list[ForecastLifecycleStub] | None, bool, bool]:
    if raw is None:
        return None, True, True
    items = _as_sequence(raw)
    if items is None:
        return None, False, True
    parsed: list[ForecastLifecycleStub] = []
    weak = not items
    for item in items:
        mapping = _as_mapping(item)
        if mapping is None:
            return None, False, True
        if _is_placeholder_mapping(mapping):
            weak = True
        parsed.append(
            ForecastLifecycleStub(
                lifecycle_id=_echo_id(mapping),
                horizon=_echo_horizon(mapping),
            )
        )
    return parsed, True, weak


def _parse_score_list(raw: object) -> tuple[list[ForecastScoreStub] | None, bool, bool]:
    if raw is None:
        return None, True, True
    items = _as_sequence(raw)
    if items is None:
        return None, False, True
    parsed: list[ForecastScoreStub] = []
    weak = not items
    for item in items:
        mapping = _as_mapping(item)
        if mapping is None:
            return None, False, True
        if _is_placeholder_mapping(mapping):
            weak = True
        parsed.append(
            ForecastScoreStub(
                score_id=_echo_id(mapping),
                horizon=_echo_horizon(mapping),
            )
        )
    return parsed, True, weak


def _parse_horizon_spec(raw: object) -> tuple[HorizonSpecStub | None, bool, bool]:
    if raw is None:
        return None, True, True
    mapping = _as_mapping(raw)
    if mapping is None:
        return None, False, True
    return (
        HorizonSpecStub(spec_id=_echo_id(mapping), horizon=_echo_horizon(mapping)),
        True,
        _is_placeholder_mapping(mapping),
    )


def _horizon_tokens_from_mapping(mapping: Mapping[str, object]) -> set[str]:
    tokens: set[str] = set()
    echoed = _echo_horizon(mapping)
    if echoed:
        tokens.add(echoed)
    for key in ("horizons", "bands"):
        values = mapping.get(key)
        items = _as_sequence(values)
        if items is None:
            continue
        for item in items:
            if isinstance(item, str) and item.strip():
                tokens.add(item.strip())
            nested = _as_mapping(item)
            nested_horizon = _echo_horizon(nested) if nested is not None else None
            if nested_horizon:
                tokens.add(nested_horizon)
    return tokens


def _horizon_tokens_from_items(raw: object) -> set[str]:
    items = _as_sequence(raw)
    if items is None:
        return set()
    tokens: set[str] = set()
    for item in items:
        mapping = _as_mapping(item)
        if mapping is None:
            continue
        tokens.update(_horizon_tokens_from_mapping(mapping))
    return tokens


def _horizons_mismatch(
    cycles: list[ForecastLifecycleStub] | None,
    scores: list[ForecastScoreStub] | None,
    spec: HorizonSpecStub | None,
    horizon_spec_raw: object,
) -> bool:
    spec_tokens: set[str] = set()
    spec_mapping = _as_mapping(horizon_spec_raw)
    if spec_mapping is not None:
        spec_tokens.update(_horizon_tokens_from_mapping(spec_mapping))
    if spec is not None and spec.horizon:
        spec_tokens.add(spec.horizon)
    item_tokens: set[str] = set()
    for item in cycles or []:
        if item.horizon:
            item_tokens.add(item.horizon)
    for item in scores or []:
        if item.horizon:
            item_tokens.add(item.horizon)
    if not spec_tokens or not item_tokens:
        return False
    return spec_tokens.isdisjoint(item_tokens)


def _item_has_resolution(mapping: Mapping[str, object]) -> bool:
    for key in _RESOLUTION_KEYS:
        if key not in mapping:
            continue
        value = mapping[key]
        if value is None or value == "":
            continue
        return True
    return False


def _has_resolution_data(forecast_lifecycles: object, forecast_scores: object) -> bool:
    for raw in (forecast_lifecycles, forecast_scores):
        items = _as_sequence(raw)
        if items is None:
            continue
        for item in items:
            mapping = _as_mapping(item)
            if mapping is not None and _item_has_resolution(mapping):
                return True
    return False


def _canonical_events(raw: object) -> object:
    items = _as_sequence(raw)
    if items is None:
        return None
    out: list[object] = []
    for item in items:
        mapping = _as_mapping(item)
        out.append(dict(mapping) if mapping is not None else None)
    return out


def _canonical_mapping(raw: object) -> object:
    mapping = _as_mapping(raw)
    return dict(mapping) if mapping is not None else None


def _input_hash(
    forecast_lifecycles: object,
    forecast_scores: object,
    horizon_spec: object,
    seed: object,
    run_id: object,
    timestamp: str | None,
    catalog_hash: object,
) -> str:
    payload = {
        "catalog_hash": catalog_hash if isinstance(catalog_hash, str) else None,
        "forecast_lifecycles": _canonical_events(forecast_lifecycles),
        "forecast_scores": _canonical_events(forecast_scores),
        "horizon_spec": _canonical_mapping(horizon_spec),
        "run_id": run_id if isinstance(run_id, str) else None,
        "seed": seed if isinstance(seed, (int, str)) and not isinstance(seed, bool) else None,
        "timestamp": timestamp,
    }
    return sha256_hex(canonical_json(payload))


def _unique_flags(flags: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for flag in flags:
        if flag not in seen:
            seen.add(flag)
            out.append(flag)
    return out


def _body(
    report: CalibrationReportStub | None,
    drift: PerformanceDriftStub | None,
    metrics: HorizonMetricsStub | None,
    flags: list[str],
) -> dict[str, object]:
    return {
        "calibration_incidents": None,
        "calibration_report": None if report is None else report.model_dump(),
        "forecast_mutation": None,
        "forecast_weights": None,
        "horizon_metrics": None if metrics is None else metrics.model_dump(),
        "live_scoring_activated": False,
        "not_computable_flags": flags,
        "performance_drift": None if drift is None else drift.model_dump(),
    }


def _finalize(
    *,
    report: CalibrationReportStub | None,
    drift: PerformanceDriftStub | None,
    metrics: HorizonMetricsStub | None,
    flags: list[str],
    path: list[str],
    input_hash: str,
    run_id: object,
    catalog_hash: object,
    timestamp: str | None,
) -> CalibrationResult:
    unique = _unique_flags(flags)
    provenance = CalibrationProvenance(
        run_id=run_id if isinstance(run_id, str) else None,
        input_hash=input_hash,
        output_hash=sha256_hex(canonical_json(_body(report, drift, metrics, unique))),
        catalog_hash=catalog_hash if isinstance(catalog_hash, str) else None,
        timestamp=timestamp,
        computation_path=list(path),
    )
    return CalibrationResult(
        calibration_report=report,
        performance_drift=drift,
        horizon_metrics=metrics,
        calibration_incidents=None,
        live_scoring_activated=False,
        forecast_mutation=None,
        forecast_weights=None,
        not_computable_flags=unique,
        provenance=provenance,
    )


def _null_result(
    *,
    flags: list[str],
    path: list[str],
    input_hash: str,
    run_id: object,
    catalog_hash: object,
    timestamp: str | None,
) -> CalibrationResult:
    return _finalize(
        report=None,
        drift=None,
        metrics=None,
        flags=flags,
        path=path,
        input_hash=input_hash,
        run_id=run_id,
        catalog_hash=catalog_hash,
        timestamp=timestamp,
    )


def _placeholder_result(
    *,
    flags: list[str],
    path: list[str],
    input_hash: str,
    run_id: object,
    catalog_hash: object,
    timestamp: str | None,
) -> CalibrationResult:
    return _finalize(
        report=CalibrationReportStub(),
        drift=PerformanceDriftStub(),
        metrics=HorizonMetricsStub(),
        flags=flags,
        path=path,
        input_hash=input_hash,
        run_id=run_id,
        catalog_hash=catalog_hash,
        timestamp=timestamp,
    )
