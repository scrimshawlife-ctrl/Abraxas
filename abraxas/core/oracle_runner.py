from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Tuple, Callable, Optional

from ..io.config import OverlaysConfig, UserConfig
from ..kernel.dispatcher import get_kernel_runner
from .tier_router import tier_context


def _sha256_json(obj: Any) -> str:
    b = json.dumps(obj, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(b).hexdigest()


@dataclass(frozen=True)
class OracleRunInputs:
    day: str
    user: Dict[str, Any]
    overlays_enabled: Dict[str, bool]
    tier_ctx: Dict[str, Any]
    checkin: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "day": self.day,
            "user": self.user,
            "overlays_enabled": self.overlays_enabled,
            "tier_ctx": self.tier_ctx,
            "checkin": self.checkin,
        }


@dataclass(frozen=True)
class OracleRunOutputs:
    readout: Dict[str, Any]
    provenance: Dict[str, Any]


def _load_engine() -> Callable[[OracleRunInputs], Dict[str, Any]]:
    return get_kernel_runner("v2")


def run_oracle(uc: UserConfig, oc: OverlaysConfig, day: str, checkin: Optional[str] = None) -> OracleRunOutputs:
    tier_ctx = tier_context(uc.tier)
    inputs = OracleRunInputs(
        day=day,
        user=uc.to_dict(),
        overlays_enabled=dict(oc.enabled),
        tier_ctx=tier_ctx,
        checkin=checkin,
    )

    engine = _load_engine()
    readout = engine(inputs)

    provenance = {
        "schema": "provenance.v0",
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "inputs_hash": _sha256_json(inputs.to_dict()),
        "tier": uc.tier,
        "admin": uc.admin,
        "overlays_enabled": dict(oc.enabled),
        "engine_entry": getattr(engine, "__name__", "unknown"),
        "note": "Offline-first run; any network fetchers must be explicit overlays and may cache locally.",
    }
    return OracleRunOutputs(readout=readout, provenance=provenance)
