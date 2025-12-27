from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Literal


CSPTag = Literal[
    "investigative",
    "plausible_unproven",
    "speculative",
    "opportunistic_op",
    "noise_halo",
    "unknown",
]


@dataclass(frozen=True)
class CSPResult:
    COH: bool
    CIP: float
    EA: float
    FF: float
    MIO: float
    tag: CSPTag
    flags: List[str]
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
