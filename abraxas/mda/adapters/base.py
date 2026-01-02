from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class AdapterResult:
    vectors: Dict[str, Any]
    notes: str = ""

