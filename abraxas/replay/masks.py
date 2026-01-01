"""
Replay Mask Implementations
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Dict, List

from abraxas.replay.types import ReplayInfluence, ReplayMask, ReplayMaskKind


def apply_mask_to_signal_events(events: List[Any], mask: ReplayMask) -> List[Any]:
    if mask.kind == ReplayMaskKind.EXCLUDE_SOURCE_LABELS:
        excluded = set(mask.params.get("source_labels", []))
        return [event for event in events if _get_attr(event, "source") not in excluded]
    if mask.kind == ReplayMaskKind.EXCLUDE_DOMAIN:
        excluded_domain = mask.params.get("domain")
        return [event for event in events if _get_attr(event, "domain") != excluded_domain]
    return list(events)


def apply_mask_to_influence_events(
    influences: List[Any], mask: ReplayMask
) -> List[Any]:
    if mask.kind == ReplayMaskKind.EXCLUDE_SOURCE_LABELS:
        excluded = set(mask.params.get("source_labels", []))
        return [inf for inf in influences if _get_attr(inf, "source_label") not in excluded]

    if mask.kind == ReplayMaskKind.EXCLUDE_QUARANTINED:
        return [inf for inf in influences if not bool(_get_attr(inf, "quarantined"))]

    if mask.kind == ReplayMaskKind.CLAMP_SIW_MAX:
        max_w = float(mask.params.get("max_w", 1.0))
        return [
            _clamp_influence_weight(inf, max_w)
            for inf in influences
        ]

    if mask.kind == ReplayMaskKind.ONLY_EVIDENCE_PACK:
        return [inf for inf in influences if _get_attr(inf, "source_class") == "evidence_pack"]

    if mask.kind == ReplayMaskKind.EXCLUDE_DOMAIN:
        excluded_domain = mask.params.get("domain")
        return [inf for inf in influences if _get_attr(inf, "domain") != excluded_domain]

    return list(influences)


def apply_mask_to_overrides(
    overrides: Dict[str, Any], mask: ReplayMask
) -> Dict[str, Any]:
    return dict(overrides)


def _get_attr(obj: Any, name: str) -> Any:
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)


def _clamp_influence_weight(influence: Any, max_w: float) -> Any:
    if isinstance(influence, ReplayInfluence):
        return replace(influence, weight=min(influence.weight, max_w))
    if isinstance(influence, dict):
        influence = dict(influence)
        key = "weight" if "weight" in influence else "strength"
        if key in influence:
            influence[key] = min(float(influence[key]), max_w)
        return influence
    if hasattr(influence, "weight"):
        influence.weight = min(float(influence.weight), max_w)
        return influence
    if hasattr(influence, "strength"):
        influence.strength = min(float(influence.strength), max_w)
        return influence
    return influence
