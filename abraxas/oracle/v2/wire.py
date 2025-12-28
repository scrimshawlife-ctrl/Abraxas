from __future__ import annotations

import hashlib
import json
from typing import Any, Dict

from abraxas.oracle.v2.compliance import build_compliance_report
from abraxas.oracle.v2.mode_router import route_mode_v2


def _stable_hash(obj: Any) -> str:
    """
    Deterministic fingerprint for mode selection stability.
    """
    b = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(b).hexdigest()


def build_v2_block(
    *,
    checks: Dict[str, Any],
    router_input: Dict[str, Any],
    config_hash: str,
    date_iso: str | None = None,
) -> Dict[str, Any]:
    """
    Produces the v2 governance block:
      - compliance report
      - deterministic mode_decision
      - provenance lock + stable fingerprint for decision stability
    """
    compliance = build_compliance_report(checks=checks, config_hash=config_hash, date_iso=date_iso)

    ri = dict(router_input)
    ri["compliance_status"] = compliance["status"]
    ri["config_hash"] = config_hash

    decision = route_mode_v2(ri)
    fp = _stable_hash({"mode": decision["mode"], "reasons": decision["reasons"]})

    return {
        "mode": decision["mode"],
        "mode_decision": {**decision, "fingerprint": fp},
        "compliance": compliance,
    }
