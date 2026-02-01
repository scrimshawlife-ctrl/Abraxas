from __future__ import annotations

from typing import Any, Dict

from aal_core.aalmanac.oracle_attachment import build_oracle_attachment_from_storage


def attach_aalmanac_shadow(oracle_packet: Dict[str, Any]) -> Dict[str, Any]:
    run_id = oracle_packet.get("oracle_packet_v0_1", {}).get("meta", {}).get("run_id")
    if not run_id:
        run_id = oracle_packet.get("oracle_packet_v0_1", {}).get("meta", {}).get("run_at", "")
    if not run_id:
        run_id = "oracle_run_unknown"

    attachment = build_oracle_attachment_from_storage(run_id=run_id)
    shadow = oracle_packet.setdefault("oracle_packet_v0_1", {}).setdefault("shadow", {})
    shadow["aalmanac"] = attachment
    return oracle_packet
