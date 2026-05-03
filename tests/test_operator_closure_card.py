from __future__ import annotations

from abraxas.operator.closure_card import run_operator_closure_card


def test_operator_card_runs() -> None:
    result = run_operator_closure_card()
    assert result["schema_version"] == "OperatorClosureCard.v1"
    assert result["health"] in ["GREEN", "YELLOW", "RED"]
    assert "registry" in result
    assert "validator" in result


def test_operator_card_deterministic() -> None:
    first = run_operator_closure_card()
    second = run_operator_closure_card()
    assert first["canonical_hash"] == second["canonical_hash"]
