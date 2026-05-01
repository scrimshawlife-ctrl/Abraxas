from __future__ import annotations

from typing import Any

from abraxas.canary.activation_models import AUTHORITY_FLAGS


def validate_activation_packet_run(report: dict[str, Any]) -> None:
    if report.get("artifact") != "CANARY-ACTIVATION-PACKET-001":
        raise ValueError("artifact mismatch")
    if report.get("schema_version") != "CanaryActivationPacketRun.v1":
        raise ValueError("schema_version mismatch")
    if report.get("authority") != AUTHORITY_FLAGS:
        raise ValueError("authority mismatch")
