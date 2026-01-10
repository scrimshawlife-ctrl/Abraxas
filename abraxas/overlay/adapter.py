from __future__ import annotations
import json
import hashlib
from typing import Any, Dict

from .schema import OverlayRequest, OverlayResponse, Phase
from .phases import dispatch


class OverlayAdapter:
    """Adapter for overlay operations providing a high-level interface."""

    def __init__(self):
        """Initialize the overlay adapter."""
        pass

    def parse_request(self, raw: str) -> OverlayRequest:
        """Parse a raw request string into an OverlayRequest.

        Args:
            raw: Raw JSON string

        Returns:
            Parsed OverlayRequest
        """
        return parse_request(raw)

    def handle(self, req: OverlayRequest) -> OverlayResponse:
        """Handle an overlay request.

        Args:
            req: The overlay request

        Returns:
            Response from handling the request
        """
        return handle(req)


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def parse_request(raw: str) -> OverlayRequest:
    obj = json.loads(raw)

    overlay = str(obj["overlay"])
    version = str(obj.get("version", "unknown"))
    phase = obj["phase"]
    if phase not in ("OPEN", "ALIGN", "ASCEND", "CLEAR", "SEAL"):
        raise ValueError("Invalid phase")

    req_id = str(obj["request_id"])
    ts = int(obj["timestamp_ms"])
    payload = obj.get("payload", {})
    if not isinstance(payload, dict):
        raise ValueError("payload must be dict")

    return OverlayRequest(
        overlay=overlay,
        version=version,
        phase=phase,  # type: ignore
        request_id=req_id,
        timestamp_ms=ts,
        payload=payload,
    )

def handle(req: OverlayRequest) -> OverlayResponse:
    payload_hash = _sha256(json.dumps(req.payload, sort_keys=True, separators=(",", ":")))
    out = dispatch(req.phase, req.payload)

    out_meta: Dict[str, Any] = {
        "overlay_version": req.version,
        "payload_hash": payload_hash,
        "timestamp_ms": req.timestamp_ms,
    }

    return OverlayResponse(
        ok=True,
        overlay=req.overlay,
        phase=req.phase,
        request_id=req.request_id,
        output={"meta": out_meta, "result": out},
        error=None,
    )
