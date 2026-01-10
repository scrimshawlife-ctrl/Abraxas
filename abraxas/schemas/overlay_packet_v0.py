from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional


OverlayStatus = Literal[
    "ok",
    "disabled",
    "not_installed",
    "not_computable",
    "error",
]


@dataclass(frozen=True)
class OverlayPacketV0:
    schema: str
    name: str
    version: str
    status: OverlayStatus
    summary: str
    evidence: List[Dict[str, Any]]
    data: Dict[str, Any]
    metrics: Dict[str, Any]
    notes: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": self.schema,
            "name": self.name,
            "version": self.version,
            "status": self.status,
            "summary": self.summary,
            "evidence": list(self.evidence),
            "data": dict(self.data),
            "metrics": dict(self.metrics),
            "notes": list(self.notes),
        }


def packet_ok(
    name: str,
    version: str,
    summary: str,
    data: Dict[str, Any],
    *,
    evidence: Optional[List[Dict[str, Any]]] = None,
    metrics: Optional[Dict[str, Any]] = None,
    notes: Optional[List[str]] = None,
) -> OverlayPacketV0:
    return OverlayPacketV0(
        schema="overlay_packet.v0",
        name=name,
        version=version,
        status="ok",
        summary=summary,
        evidence=evidence or [],
        data=data,
        metrics=metrics or {},
        notes=notes or [],
    )


def packet_disabled(name: str, version: str, reason: str) -> OverlayPacketV0:
    return OverlayPacketV0(
        schema="overlay_packet.v0",
        name=name,
        version=version,
        status="disabled",
        summary=reason,
        evidence=[],
        data={},
        metrics={},
        notes=[],
    )


def packet_not_installed(name: str, version: str, reason: str) -> OverlayPacketV0:
    return OverlayPacketV0(
        schema="overlay_packet.v0",
        name=name,
        version=version,
        status="not_installed",
        summary=reason,
        evidence=[],
        data={},
        metrics={},
        notes=[],
    )


def packet_not_computable(name: str, version: str, reason: str) -> OverlayPacketV0:
    return OverlayPacketV0(
        schema="overlay_packet.v0",
        name=name,
        version=version,
        status="not_computable",
        summary=reason,
        evidence=[],
        data={},
        metrics={},
        notes=[],
    )


def packet_error(name: str, version: str, err: str) -> OverlayPacketV0:
    return OverlayPacketV0(
        schema="overlay_packet.v0",
        name=name,
        version=version,
        status="error",
        summary="Overlay error",
        evidence=[],
        data={"error": err},
        metrics={},
        notes=["Check logs; overlay must never crash the oracle runner."],
    )
