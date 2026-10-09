from __future__ import annotations

import pytest
from unittest.mock import patch


def test_main_uses_real_adapter_when_not_mock():
    """Failing test: when --mock is false, must not silently use MockDomainAdapter."""
    from scripts.run_production_pipeline import main
    # This will fail until the TODO is addressed
    with patch("argparse.ArgumentParser.parse_args") as mock_parse:
        mock_parse.return_value = type("Args", (), {"domains": ["politics"], "mock": False, "output": "/tmp", "interval": 1})()
        with patch("scripts.run_production_pipeline.ProductionPipeline"):
            with pytest.raises(NotImplementedError, match="Real adapters"):
                main()