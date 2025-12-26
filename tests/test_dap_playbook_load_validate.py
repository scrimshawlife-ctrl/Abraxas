"""
Tests for DAP playbook load and validation.
"""

from abraxas.acquire.playbook import load_playbook_yaml, validate_playbook


def test_dap_playbook_load_validate():
    playbook = load_playbook_yaml("tests/fixtures/acquire/playbook_sample.yaml")
    rules = validate_playbook(playbook)
    assert playbook["version"] == "0.1"
    assert len(rules) == 1
