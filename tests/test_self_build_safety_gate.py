from __future__ import annotations

from abraxas.registry.self_build_safety_gate import run_self_build_safety_gate


def test_safety_gate() -> None:
    result = run_self_build_safety_gate()
    assert result["schema_version"] == "SelfBuildSafetyReport.v1"
    assert result["green_state_verified"] is True
