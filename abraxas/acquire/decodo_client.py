from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class DecodoStatus:
    available: bool
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def decodo_status() -> DecodoStatus:
    """
    Deterministic availability check. No network calls here.
    """
    key = os.getenv("DECODO_API_KEY") or os.getenv("DECODO_KEY") or ""
    if not key.strip():
        return DecodoStatus(available=False, reason="missing_env_DECODO_API_KEY")
    return DecodoStatus(available=True, reason="env_present")


def build_decodo_query(term: str, *, domains: Optional[list[str]] = None) -> Dict[str, Any]:
    """
    A declarative query object. The actual Decodo runner can interpret this.
    """
    return {"q": term, "domains": domains or []}
