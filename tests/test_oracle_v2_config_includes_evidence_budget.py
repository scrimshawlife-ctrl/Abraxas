from __future__ import annotations

from abraxas.oracle.v2.config import default_config


def test_default_config_includes_evidence_budget_bytes():
    """Test that default_config includes evidence_budget_bytes in features."""
    cfg = default_config()
    assert "features" in cfg
    assert "evidence_budget_bytes" in cfg["features"]
    assert isinstance(cfg["features"]["evidence_budget_bytes"], int)
    assert cfg["features"]["evidence_budget_bytes"] > 0
