from __future__ import annotations

from abx.rune_contracts import load_abx_rune_contracts


def test_load_abx_rune_contracts_has_expected_shape() -> None:
    contracts = load_abx_rune_contracts()
    assert contracts

    for contract in contracts:
        assert contract.rune_id
        assert contract.acronym
        assert contract.version
        assert isinstance(contract.inputs, list)
        assert isinstance(contract.outputs, list)
        assert contract.influence_policy in {"NONE", "BOUNDED", "DIRECT"}
        assert "run_id" in contract.provenance_fields


def test_load_abx_rune_contracts_is_deterministic() -> None:
    first = [contract.model_dump() for contract in load_abx_rune_contracts()]
    second = [contract.model_dump() for contract in load_abx_rune_contracts()]
    assert first == second
