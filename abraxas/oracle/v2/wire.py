from __future__ import annotations

import hashlib
import json
from typing import Any, Dict

from abraxas.oracle.v2.compliance import build_compliance_report, _config_fingerprint
from abraxas.oracle.v2.mode_router import route_mode_v2


def _stable_hash(obj: Any) -> str:
    """
    Deterministic fingerprint for mode selection stability.
    """
    b = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(b).hexdigest()


def build_mode_decision(
    *,
    router_input: Dict[str, Any],
    config_hash: str,
    user_mode_request: str | None = None,
    config_payload: Dict[str, Any] | None = None,
    config_source: str | None = None,
) -> Dict[str, Any]:
    """
    Deterministically choose and fingerprint mode decision.
    """
    # Route mode based on inputs
    ri = dict(router_input)
    ri["config_hash"] = config_hash
    if user_mode_request:
        ri["user_mode_request"] = user_mode_request

    decision = route_mode_v2(ri)

    # Build provenance
    provenance = {"config_hash": config_hash}
    cfp = _config_fingerprint(config_payload)
    if cfp is not None:
        provenance["config_fingerprint"] = cfp
    if isinstance(config_source, str) and config_source.strip():
        provenance["config_source"] = config_source

    # Add provenance and fingerprint to decision
    out = {**decision, "provenance": provenance}
    out["fingerprint"] = _stable_hash({"mode": out["mode"], "reasons": out["reasons"]})

    return out


def build_v2_block(
    *,
    checks: Dict[str, Any],
    router_input: Dict[str, Any],
    config_hash: str,
    date_iso: str | None = None,
    config_payload: Dict[str, Any] | None = None,
    config_source: str | None = None,
) -> Dict[str, Any]:
    """
    Produces the v2 governance block:
      - compliance report
      - deterministic mode_decision
      - provenance lock + stable fingerprint for decision stability
    """
    compliance = build_compliance_report(
        checks=checks,
        config_hash=config_hash,
        date_iso=date_iso,
        config_payload=config_payload,
        config_source=config_source,
    )

    ri = dict(router_input)
    ri["compliance_status"] = compliance["status"]

    mode_decision = build_mode_decision(
        router_input=ri,
        config_hash=config_hash,
        config_payload=config_payload,
        config_source=config_source,
    )

    return {
        "mode": mode_decision["mode"],
        "mode_decision": mode_decision,
        "compliance": compliance,
    }
