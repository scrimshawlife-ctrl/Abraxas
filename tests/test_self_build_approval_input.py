from __future__ import annotations

from abraxas.registry.self_build_approval_input import load_self_build_approval_input


def test_approval_input_defaults() -> None:
    result = load_self_build_approval_input("out/registry/approval_input_missing_for_test.json")
    assert result["schema_version"] == "SelfBuildApprovalInput.v1"
    assert result["approved_ids"] == []
    assert result["rejected_ids"] == []
