"""
Counterfactual Replay Types
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class ReplayMaskKind(str, Enum):
    EXCLUDE_SOURCE_LABELS = "EXCLUDE_SOURCE_LABELS"
    EXCLUDE_QUARANTINED = "EXCLUDE_QUARANTINED"
    CLAMP_SIW_MAX = "CLAMP_SIW_MAX"
    ONLY_EVIDENCE_PACK = "ONLY_EVIDENCE_PACK"
    EXCLUDE_DOMAIN = "EXCLUDE_DOMAIN"


@dataclass(frozen=True)
class ReplayMask:
    mask_id: str
    kind: ReplayMaskKind
    params: Dict[str, Any]
    description: str


@dataclass(frozen=True)
class ReplayInfluence:
    influence_id: str
    source_label: Optional[str]
    quarantined: bool
    weight: float
    source_class: Optional[str]
    domain: Optional[str]
