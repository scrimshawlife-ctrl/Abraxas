from __future__ import annotations

import pytest
from unittest.mock import patch


def test_main_raises_not_implemented_for_unimplemented_domains():
    """Domains without real adapters must still raise NotImplementedError."""
    from scripts.run_production_pipeline import main
    with patch("argparse.ArgumentParser.parse_args") as mock_parse:
        mock_parse.return_value = type("Args", (), {"domains": ["media", "finance"], "mock": False, "output": "/tmp", "interval": 1})()
        with patch("scripts.run_production_pipeline.ProductionPipeline"):
            with pytest.raises(NotImplementedError, match="Real adapters"):
                main()


def test_politics_domain_adapter_implements_interface():
    """Real adapter for politics domain must produce valid DomainSnapshot."""
    from abraxas.adapters.politics_domain_adapter import PoliticsDomainAdapter
    from abraxas.adapters.domain_data import DomainSnapshot
    adapter = PoliticsDomainAdapter(domain="politics")
    snap = adapter.fetch_current_state()
    assert isinstance(snap, DomainSnapshot)
    assert snap.domain == "politics"
    assert len(snap.tokens) >= 1
    assert snap.source == "politics-adapter"


def test_main_uses_real_adapter_for_politics_when_not_mock():
    """When --mock is false, politics domain must use real adapter without raising."""
    from scripts.run_production_pipeline import main
    with patch("argparse.ArgumentParser.parse_args") as mock_parse:
        mock_parse.return_value = type("Args", (), {"domains": ["politics"], "mock": False, "output": "/tmp", "interval": 1})()
        with patch("scripts.run_production_pipeline.ProductionPipeline"), \
             patch("scripts.run_production_pipeline.PoliticsDomainAdapter") as mock_adapter:
            main()
            mock_adapter.assert_called_once_with(domain="politics")