"""Pinned locks for the TimesFM 2.5 Shadow lab.

These values are the slice contract. Callers must not promote them
into Forecast, Canon Registry, or Rune Active.
"""

from __future__ import annotations

from typing import Literal

ADAPTER_ID = "timesfm_local_2_5"
PACKET_TYPE = "TimesFMShadowForecast.v0"
LANE: Literal["SHADOW"] = "SHADOW"
INFLUENCE_POLICY: Literal["NONE"] = "NONE"
VALID_FOR_FORECAST = False
MODEL_ID = "google/timesfm-2.5-200m-transformers"
HF_REVISION = "5a9806b9b291fad9233b5249d88263f1846304d3"
LICENSE = "Apache-2.0"
SOURCE_ID = "EXT.ENERGY_CHARTS.PRICE.v1"
ATLAS_SOURCE_ID = "ENERGY_CHARTS_PRICE_V1"
BZN = "DE-LU"
ENERGY_CHARTS_PRICE_URL = "https://api.energy-charts.info/price?bzn=DE-LU"
SEMANTICS = "generative_prior_not_objective_probability"
DEFAULT_SEED = 20260906
DEFAULT_HORIZON = 24
DEFAULT_WINDOW_N = 256
DEFAULT_TIMEOUT_S = 30
DEFAULT_OUT_DIR = "out/timesfm_shadow"
LATEST_PACKET_NAME = "timesfm_shadow_forecast.v0.latest.json"

# Code-only stub. Not minted in Canon Registry / Active.
RUNE_TIMESFM_FORECAST = "RUNE.TIMESFM_FORECAST"
RUNE_TIMESFM_FORECAST_KIND = "code_only_stub"
MONTE_FORECAST_FEED = "MONTE_FORECAST"
BIAS_DELTA_FEED = "BIAS_DELTA"

STANDARD_QUANTILES = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)
Q10 = 0.1
Q50 = 0.5
Q90 = 0.9
MAX_CONTEXT_LEN = 1024
FORBIDDEN_MODEL_MARKERS = ("timesfm-3", "timesfm_3", "timesfm3")
