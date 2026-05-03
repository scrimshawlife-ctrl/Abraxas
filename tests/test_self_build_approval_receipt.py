from __future__ import annotations

from abraxas.registry.self_build_approval_receipt import run_self_build_approval_receipt


def test_approval_receipt() -> None:
    result = run_self_build_approval_receipt([], [])
    assert result["schema_version"] == "SelfBuildApprovalReceipt.v1"
    assert result["approval_count"] >= 1
