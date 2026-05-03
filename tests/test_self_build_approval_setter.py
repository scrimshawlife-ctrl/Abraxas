from __future__ import annotations

from abraxas.registry.self_build_approval_setter import run_self_build_approval_setter


def test_reject_unknown_ids() -> None:
    result = run_self_build_approval_setter(["fake_id"], [])
    assert result["status"] == "INVALID_INPUT"
