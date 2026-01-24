from __future__ import annotations

import math
from dataclasses import dataclass

from .scoring import stable_round


@dataclass(frozen=True)
class SASParams:
    """
    Deterministic salience score per (subword) per day.
    This is *not* semantic. It's recurrence + diversity + stability.
    """
    w_count: float = 1.0
    w_sources: float = 0.8
    w_events: float = 0.6
    w_len: float = 0.15  # tiny bias toward longer subs (less trivial)
    max_len_bonus: int = 8


def _log1p(x: float) -> float:
    return math.log1p(max(0.0, x))


def compute_sas_for_sub(
    *,
    mentions: int,
    sources_count: int,
    events_count: int,
    sub_len: int,
    params: SASParams,
) -> float:
    """
    SAS = w_count*log1p(mentions) + w_sources*log1p(sources) + w_events*log1p(events) + w_len*len_bonus
    Deterministic. Bounded-ish.
    """
    len_bonus = min(max(0, sub_len - 2), params.max_len_bonus)  # 3->1 ... capped
    score = (
        params.w_count * _log1p(mentions)
        + params.w_sources * _log1p(sources_count)
        + params.w_events * _log1p(events_count)
        + params.w_len * float(len_bonus)
    )
    return stable_round(score, 6)
