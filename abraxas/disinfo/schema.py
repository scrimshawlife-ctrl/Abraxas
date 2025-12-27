from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Literal


Bucket = Literal["LOW", "MED", "HIGH", "UNKNOWN"]


@dataclass(frozen=True)
class DisinfoMetric:
    name: str
    score: float
    bucket: Bucket
    flags: List[str]
    refs: List[str]
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
