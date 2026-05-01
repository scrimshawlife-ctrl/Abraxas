from __future__ import annotations

from typing import Any

from abraxas.canary.activation_models import AUTHORITY_FLAGS
from abraxas.canary.activation_packet import build_activation_packets
from abraxas.canary.activation_validator import validate_activation_packet_run


def build_canary_activation_packet_run(
    review_gate_run: dict[str, Any],
    overlay_run: dict[str, Any],
    ledger_run: dict[str, Any],
) -> dict[str, Any]:
    packets, skipped = build_activation_packets(review_gate_run, overlay_run, ledger_run)
    recommendations_total = len(review_gate_run.get("recommendations", [])) if isinstance(review_gate_run.get("recommendations"), list) else 0
    report = {
        "artifact": "CANARY-ACTIVATION-PACKET-001",
        "schema_version": "CanaryActivationPacketRun.v1",
        "authority": dict(AUTHORITY_FLAGS),
        "counts": {
            "recommendations_total": recommendations_total,
            "packets_created": len(packets),
            "skipped": len(skipped),
        },
        "packets": packets,
        "skipped_recommendations": skipped,
    }
    validate_activation_packet_run(report)
    return report
