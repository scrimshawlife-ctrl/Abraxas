"""
Signal Marginal Value (SMV) Types
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any


class SMVUnitKind(str, Enum):
    SOURCE_LABEL = "SOURCE_LABEL"
    VECTOR_NODE = "VECTOR_NODE"
    DOMAIN = "DOMAIN"
    CLASS = "CLASS"


@dataclass(frozen=True)
class SMVUnit:
    unit_id: str
    kind: SMVUnitKind
    selectors: Dict[str, Any]
    description: str
