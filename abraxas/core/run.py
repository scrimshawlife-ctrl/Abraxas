from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any
from .context import UserContext
from .state import OracleState


@dataclass(frozen=True)
class OracleRun:
    run_id: str
    user: UserContext
    state: OracleState
    emitted: Dict[str, Any]  # final tier-filtered output
    # Always store provenance summary even if parts omitted.
    provenance: Dict[str, Any]
