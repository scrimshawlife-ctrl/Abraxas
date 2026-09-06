"""TimesFMShadowForecast.v0 packet schema and lock checks."""

from __future__ import annotations

from typing import Literal, Mapping, Sequence

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

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

    @model_validator(mode="after")
    def _aligned(self) -> "HistoryBlock":
        if len(self.timestamps) != len(self.values):
            raise ValueError("history timestamps and values must have equal length")
        if self.window_n != len(self.values):
            raise ValueError("history window_n must equal values length")
        if self.window_n < 1:
            raise ValueError("history window_n must be >= 1")
        return self


class ForecastBlock(BaseModel):
    horizon: int
    mean: list[float]
    quantiles: dict[str, list[float]]

    @model_validator(mode="after")
    def _aligned(self) -> "ForecastBlock":
        if self.horizon < 1:
            raise ValueError("forecast horizon must be >= 1")
        if len(self.mean) != self.horizon:
            raise ValueError("forecast mean length must equal horizon")
        for key in ("q10", "q50", "q90"):
            series = self.quantiles.get(key)
            if not isinstance(series, list) or len(series) != self.horizon:
                raise ValueError(f"forecast quantiles.{key} length must equal horizon")
        return self


class FoldInFeed(BaseModel):
    target: str
    lane: Literal["SHADOW"] = LANE
    authority: Literal["none"] = "none"
    writes_objective_probability: bool = False

    @model_validator(mode="after")
    def _shadow_only(self) -> "FoldInFeed":
        if self.lane != LANE:
            raise ValueError("fold_in feeds remain SHADOW only")
        if self.authority != "none":
            raise ValueError("fold_in feeds have no authority")
        if self.writes_objective_probability:
            raise ValueError("TimesFM must not write objective_probability")
        return self


class FoldInBlock(BaseModel):
    feeds: list[FoldInFeed]


class TimesFMShadowForecastV0(BaseModel):
    """Local Shadow evidence packet. Not Canon. Not Forecast-active."""

    model_config = ConfigDict(extra="forbid")

    packet_type: Literal["TimesFMShadowForecast.v0"] = PACKET_TYPE
    lane: Literal["SHADOW"] = LANE
    influence_policy: Literal["NONE"] = INFLUENCE_POLICY
    valid_for_forecast: Literal[False] = VALID_FOR_FORECAST
    model_id: Literal["google/timesfm-2.5-200m-transformers"] = MODEL_ID
    hf_revision: str = Field(min_length=7)
    license: Literal["Apache-2.0"] = LICENSE
    seed: int
    source_id: Literal["EXT.ENERGY_CHARTS.PRICE.v1"] = SOURCE_ID
    bzn: Literal["DE-LU"] = BZN
    history: HistoryBlock
    forecast: ForecastBlock
    semantics: Literal["generative_prior_not_objective_probability"] = SEMANTICS
    fold_in: FoldInBlock

    @field_validator("hf_revision")
    @classmethod
    def _revision_is_pin(cls, value: str) -> str:
        if value != HF_REVISION:
            raise ValueError(f"hf_revision must equal pinned {HF_REVISION}")
        return value

    @field_validator("model_id")
    @classmethod
    def _model_is_2_5(cls, value: str) -> str:
        lowered = value.lower()
        if any(marker in lowered for marker in FORBIDDEN_MODEL_MARKERS):
            raise ValueError("TimesFM 3.0 and non-2.5 ids are forbidden")
        if value != MODEL_ID:
            raise ValueError(f"model_id must equal {MODEL_ID}")
        return value

    @model_validator(mode="after")
    def _locks(self) -> "TimesFMShadowForecastV0":
        if self.valid_for_forecast is not False:
            raise ValueError("valid_for_forecast must stay false")
        if "objective_probability" in self.model_dump():
            raise ValueError("packet must not carry objective_probability")
        return self

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
    if packet.valid_for_forecast is not False:
        raise ValueError("valid_for_forecast must be false")
    if packet.license != LICENSE:
        raise ValueError("license must be Apache-2.0")
    if packet.model_id != MODEL_ID:
        raise ValueError("model_id lock failed")
    if packet.hf_revision != HF_REVISION:
        raise ValueError("hf_revision lock failed")
    if packet.lane != LANE or packet.influence_policy != INFLUENCE_POLICY:
        raise ValueError("lane lock failed")
    if packet.semantics != SEMANTICS:
        raise ValueError("semantics lock failed")
    targets = {feed.target: feed for feed in packet.fold_in.feeds}
    if RUNE_TIMESFM_FORECAST not in targets:
        raise ValueError("missing RUNE.TIMESFM_FORECAST fold_in feed")
    bias = targets.get(BIAS_DELTA_FEED)
    if bias is None or bias.writes_objective_probability:
        raise ValueError("BIAS_DELTA must be SHADOW and must not write objective_probability")
    if any(feed.lane != LANE for feed in packet.fold_in.feeds):
        raise ValueError("fold_in feeds must stay SHADOW")
