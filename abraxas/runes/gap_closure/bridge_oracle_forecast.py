from __future__ import annotations

from typing import Any

from abraxas.core.canonical import canonical_json, sha256_hex


def build_oracle_forecast_bridge_packet(run_record: dict[str, Any]) -> dict[str, Any]:
    basis = {
        "run_id": run_record["run_id"],
        "input_hash": run_record["input_hash"],
        "status": run_record["status"],
    }
    return {
        "schema_version": "oracle_forecast_bridge_packet.v1",
        "packet_id": sha256_hex(canonical_json(basis))[:16],
        "run_id": run_record["run_id"],
        "input_hash": run_record["input_hash"],
        "forecast_candidates": [],
        "outcome_bindings": [],
        "status": run_record["status"],
        "promotion_recommendation": "HOLD",
    }
