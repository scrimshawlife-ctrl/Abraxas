from __future__ import annotations

import math
from dataclasses import dataclass

from .scoring import stable_round


@dataclass(frozen=True)
class LPSParams:
    # weights
    w_tap: float = 1.0
    w_sas: float = 0.6
    w_pfdi: float = 0.8
    w_src: float = 0.5
    w_evt: float = 0.4
    w_age: float = 0.7  # encourages persistence
    w_decay: float = 0.9  # penalize “spike then vanish”

    # gates
    min_days_shadow: int = 3
    min_days_canary: int = 7
    min_days_core: int = 14
    min_sources_canary: int = 2
    min_events_canary: int = 2
    min_sources_core: int = 3
    min_events_core: int = 3

    # thresholds
    thr_shadow: float = 1.2
    thr_canary: float = 2.4
    thr_core: float = 3.2


def _log1p(x: float) -> float:
    return math.log1p(max(0.0, x))


def compute_lps(
    *,
    tap_max: float,
    sas_sum: float,
    pfdi_max: float,
    days_seen: int,
    sources_count: int,
    events_count: int,
    mentions_total: int,
    params: LPSParams,
) -> float:
    """
    Deterministic Lexicon Promotion Score.
    - tap_max: already ~0-? (small)
    - sas_sum: grows with repeated salience
    - pfdi_max: drift spikes
    - age: log(days_seen)
    - diversity: log(sources/events)
    - decay: penalize very high mentions without persistence (proxy)
    """
    age = _log1p(days_seen)
    src = _log1p(sources_count)
    evt = _log1p(events_count)

    # crude “spike” penalty: huge mentions but low days_seen
    spike_ratio = mentions_total / max(1, days_seen)
    decay_pen = _log1p(max(0.0, spike_ratio - 5.0))  # only penalize once >5/day

    score = (
        params.w_tap * tap_max
        + params.w_sas * _log1p(sas_sum)
        + params.w_pfdi * max(0.0, pfdi_max)
        + params.w_src * src
        + params.w_evt * evt
        + params.w_age * age
        - params.w_decay * decay_pen
    )
    return stable_round(score, 6)


def lane_decision(
    *,
    lps: float,
    days_seen: int,
    sources_count: int,
    events_count: int,
    params: LPSParams,
) -> str:
    """
    Pure decision function: returns lane target.
    Gates first, then thresholds.
    """
    # core gates
    if (
        days_seen >= params.min_days_core
        and sources_count >= params.min_sources_core
        and events_count >= params.min_events_core
        and lps >= params.thr_core
    ):
        return "core"

    # canary gates
    if (
        days_seen >= params.min_days_canary
        and sources_count >= params.min_sources_canary
        and events_count >= params.min_events_canary
        and lps >= params.thr_canary
    ):
        return "canary"

    # shadow gates
    if days_seen >= params.min_days_shadow and lps >= params.thr_shadow:
        return "shadow"

    return "candidate"
