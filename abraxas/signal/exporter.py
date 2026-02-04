from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
import uuid

from abraxas.util.canonical_hash import canonical_hash

Tier = Literal["psychonaut", "academic", "enterprise"]
Lane = Literal["canon", "shadow", "sandbox"]
ProvStatus = Literal["complete", "partial", "missing"]
InvStatus = Literal["pass", "fail", "not_evaluated"]
RentStatus = Literal["paid", "unpaid", "not_applicable"]


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _signal_id_from_run_id(run_id: str) -> str:
    digest = canonical_hash({"run_id": run_id})
    return f"sig_{digest[:16]}"


def emit_signal_packet(
    *,
    payload: Dict[str, Any],
    tier: Tier,
    lane: Lane,
    confidence: Optional[Dict[str, Any]] = None,
    provenance_status: Optional[ProvStatus] = None,
    invariance_status: Optional[InvStatus] = None,
    drift_flags: Optional[List[str]] = None,
    rent_status: Optional[RentStatus] = None,
    not_computable_regions: Optional[List[Dict[str, Any]]] = None,
    run_id: Optional[str] = None,
    timestamp_utc: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Emit an AbraxasSignalPacket.v0-compatible dict.

    Conservative defaults are applied when optional fields are not provided.
    """
    signal_id = _signal_id_from_run_id(run_id) if run_id else f"sig_{uuid.uuid4().hex[:16]}"
    return {
        "signal_id": signal_id,
        "timestamp_utc": timestamp_utc or _now_utc(),
        "tier": tier,
        "lane": lane,
        "payload": payload,
        "confidence": confidence if confidence is not None else {},
        "provenance_status": provenance_status or "partial",
        "invariance_status": invariance_status or "not_evaluated",
        "drift_flags": drift_flags if drift_flags is not None else [],
        "rent_status": rent_status or "not_applicable",
        "not_computable_regions": not_computable_regions if not_computable_regions is not None else [],
    }
