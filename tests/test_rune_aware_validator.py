# tests/test_rune_aware_validator.py
import pytest

from abx.execution_validator import _surface_rune_info

def test_validator_surfaces_rune_id_and_phase():
    # mock row with rune
    row = {"rune_id": "RUNE.INGEST", "phase": "proto"}
    # call validator surfacing
    surfaced = _surface_rune_info(row)
    assert surfaced["rune_id"] == "RUNE.INGEST"
    assert "phase" in surfaced
    print("Rune surfacing test passed")