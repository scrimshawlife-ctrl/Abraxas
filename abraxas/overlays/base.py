from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict
from ..core.state import OracleState
from ..core.context import UserContext


@dataclass(frozen=True)
class OverlayMeta:
    name: str
    version: str
    required_signals: tuple
    output_schema: str


class AbraxasOverlay:
    meta: OverlayMeta

    def run(self, oracle_state: OracleState, user: UserContext) -> Dict[str, Any]:
        raise NotImplementedError
