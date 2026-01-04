"""Rune adapters for forecast.* capability contracts.

Thin wrappers only: no core logic changes.
"""

from __future__ import annotations

from typing import Any, Dict, List

from abraxas.forecast.horizon_bins import horizon_bucket as _horizon_bucket
from abraxas.forecast.policy_candidates import candidates_v0_1 as _candidates_v0_1
from abraxas.forecast.scoring import brier_score as _brier_score
from abraxas.forecast.term_class_map import load_term_class_map as _load_term_class_map


def brier_score_deterministic(probs: List[float], outcomes: List[int], **kwargs) -> Dict[str, Any]:
    return {"brier": float(_brier_score(probs, outcomes))}


def horizon_bucket_deterministic(horizon: Any, **kwargs) -> Dict[str, Any]:
    return {"bucket": str(_horizon_bucket(horizon))}


def policy_candidates_v0_1_deterministic(**kwargs) -> Dict[str, Any]:
    return {"candidates": _candidates_v0_1()}


def load_term_class_map_deterministic(a2_phase_path: str, **kwargs) -> Dict[str, Any]:
    return {"term_class_map": _load_term_class_map(a2_phase_path)}


__all__ = [
    "brier_score_deterministic",
    "horizon_bucket_deterministic",
    "policy_candidates_v0_1_deterministic",
    "load_term_class_map_deterministic",
]

