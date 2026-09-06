"""TimesFMShadowForecast.v0 packet schema and lock checks."""

from __future__ import annotations

from typing import Literal, Mapping, Sequence

from pydantic import BaseModel, Field, ValidationError

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.sources.timesfm_shadow.constants import (
    BIAS_DELTA_FEED,
    BZN,
    FORBIDDEN_MODEL_MARKERS,
    HF_REVISION,
    INFLUENCE_POLICY,
    LANE,
    LICENSE,
    MODEL_ID,
    MONTE_FORECAST_FEED,
    PACKET_TYPE,
    RUNE_TIMESFM_FORECAST,
    SEMANTICS,
    SOURCE_ID,
    VALID_FOR_FORECAST,
)


class HistoryBlock(BaseModel):
    timestamps: list[str]
    values: list[float]
    window_n: int


class ForecastBlock(BaseModel):
    horizon: int
    mean: list[float]
    quantiles: dict[str, list[float]]


class FoldInFeed(BaseModel):
    target: str
    lane: Literal["SHADOW"] = LANE
    authority: Literal["none"] = "none"
    writes_objective_probability: bool = False


class FoldInBlock(BaseModel):
    feeds: list[FoldInFeed]


class TimesFMShadowForecastV0(BaseModel):
    """Local Shadow evidence packet. Not Canon. Not Forecast-active."""

    packet_type: Literal["TimesFMShadowForecast.v0"] = PACKET_TYPE
    lane: Literal["SHADOW"] = LANE
    influence_policy: Literal["NONE"] = INFLUENCE_POLICY
    valid_for_forecast: bool = VALID_FOR_FORECAST
    model_id: str = MODEL_ID
    hf_revision: str = Field()
    license: str = LICENSE
    seed: int
    source_id: str = SOURCE_ID
    bzn: str = BZN
    history: HistoryBlock
    forecast: ForecastBlock
    semantics: str = SEMANTICS
    fold_in: FoldInBlock

    def packet_hash(self) -> str:
        return sha256_hex(canonical_json(self.model_dump()))


def default_fold_in() -> FoldInBlock:
    return FoldInBlock(
        feeds=[
            FoldInFeed(target=RUNE_TIMESFM_FORECAST),
            FoldInFeed(target=MONTE_FORECAST_FEED),
            FoldInFeed(target=BIAS_DELTA_FEED, writes_objective_probability=False),
        ]
    )


def build_shadow_packet(
    *,
    history: HistoryBlock,
    mean: Sequence[float],
    quantiles: Mapping[str, Sequence[float]],
    horizon: int,
    seed: int,
    hf_revision: str,
) -> TimesFMShadowForecastV0:
    packet = TimesFMShadowForecastV0(
        hf_revision=hf_revision,
        seed=seed,
        history=history,
        forecast=ForecastBlock(
            horizon=horizon,
            mean=[float(item) for item in mean],
            quantiles={
                "q10": [float(item) for item in quantiles["q10"]],
                "q50": [float(item) for item in quantiles["q50"]],
                "q90": [float(item) for item in quantiles["q90"]],
            },
        ),
        fold_in=default_fold_in(),
    )
    assert_shadow_locks(packet)
    return packet


def assert_shadow_locks(packet: TimesFMShadowForecastV0) -> None:
    _require(packet.valid_for_forecast is False, "valid_for_forecast must be false")
    _require(packet.license == LICENSE, "license must be Apache-2.0")
    _require(_not_timesfm_3(packet.model_id), "TimesFM 3.0 and non-2.5 ids are forbidden")
    _require(packet.model_id == MODEL_ID, "model_id lock failed")
    _require(packet.hf_revision == HF_REVISION, "hf_revision lock failed")
    _require(len(packet.hf_revision) >= 7, "hf_revision must be a commit SHA")
    _require(packet.lane == LANE and packet.influence_policy == INFLUENCE_POLICY, "lane lock failed")
    _require(packet.semantics == SEMANTICS, "semantics lock failed")
    _require(packet.packet_type == PACKET_TYPE, "packet_type lock failed")
    _require(packet.source_id == SOURCE_ID, "source_id lock failed")
    _require(packet.bzn == BZN, "bzn lock failed")
    _require("objective_probability" not in packet.model_dump(), "packet must not carry objective_probability")
    _validate_history(packet.history)
    _validate_forecast(packet.forecast)
    _validate_fold_in(packet.fold_in)


def _validate_history(history: HistoryBlock) -> None:
    _require(len(history.timestamps) == len(history.values), "history timestamps and values must have equal length")
    _require(history.window_n == len(history.values), "history window_n must equal values length")
    _require(history.window_n >= 1, "history window_n must be >= 1")


def _validate_forecast(forecast: ForecastBlock) -> None:
    _require(forecast.horizon >= 1, "forecast horizon must be >= 1")
    _require(len(forecast.mean) == forecast.horizon, "forecast mean length must equal horizon")
    for key in ("q10", "q50", "q90"):
        series = forecast.quantiles.get(key)
        _require(isinstance(series, list) and len(series) == forecast.horizon, f"forecast quantiles.{key} length must equal horizon")


def _validate_fold_in(fold_in: FoldInBlock) -> None:
    targets = {feed.target: feed for feed in fold_in.feeds}
    _require(RUNE_TIMESFM_FORECAST in targets, "missing RUNE.TIMESFM_FORECAST fold_in feed")
    bias = targets.get(BIAS_DELTA_FEED)
    _require(bias is not None, "missing BIAS_DELTA fold_in feed")
    _require(bias.writes_objective_probability is False, "BIAS_DELTA must not write objective_probability")
    for feed in fold_in.feeds:
        _require(feed.lane == LANE, "fold_in feeds must stay SHADOW")
        _require(feed.authority == "none", "fold_in feeds have no authority")
        _require(feed.writes_objective_probability is False, "TimesFM must not write objective_probability")


def _not_timesfm_3(model_id: str) -> bool:
    lowered = model_id.lower()
    return not any(marker in lowered for marker in FORBIDDEN_MODEL_MARKERS)


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise ValidationError(message)
