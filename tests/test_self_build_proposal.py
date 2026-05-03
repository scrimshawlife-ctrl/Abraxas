from __future__ import annotations

from abraxas.registry.self_build_proposal import run_self_build_proposal


def test_self_build_proposal() -> None:
    result = run_self_build_proposal()
    assert result["schema_version"] == "SelfBuildProposal.v1"
    assert "proposals" in result
