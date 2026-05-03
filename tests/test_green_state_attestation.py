from __future__ import annotations

from abraxas.registry.green_state_attestation import run_green_state_attestation


def test_green_state_receipt() -> None:
    result = run_green_state_attestation()
    assert result["schema_version"] == "GreenStateReceipt.v1"
    assert result["validator"] == "PASS"
    assert result["operator_health"] == "GREEN"
