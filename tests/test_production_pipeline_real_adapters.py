from __future__ import annotations

from unittest.mock import patch

import pytest


def test_main_raises_not_implemented_for_unimplemented_domains():
    """Domains without real adapters must still raise NotImplementedError."""
    from scripts.run_production_pipeline import main
    with patch("argparse.ArgumentParser.parse_args") as mock_parse, \
         patch("scripts.run_production_pipeline.ProductionPipeline"):
        mock_parse.return_value = type("Args", (), {"domains": ["unknown"], "mock": False, "output": "/tmp", "interval": 1})()
        with pytest.raises(NotImplementedError, match="Real adapters"):
            main()


def test_politics_domain_adapter_implements_interface():
    """Real adapter for politics domain must produce valid DomainSnapshot."""
    from abraxas.adapters.domain_data import DomainSnapshot
    from abraxas.adapters.politics_domain_adapter import PoliticsDomainAdapter
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
def test_media_domain_adapter_implements_interface():
    """Real adapter for media domain must produce valid DomainSnapshot."""
    from abraxas.adapters.domain_data import DomainSnapshot
    from abraxas.adapters.media_domain_adapter import MediaDomainAdapter
    adapter = MediaDomainAdapter(domain="media")
    snap = adapter.fetch_current_state()
    assert isinstance(snap, DomainSnapshot)
    assert snap.domain == "media"
    assert len(snap.tokens) >= 1
    assert snap.source == "media-adapter"

def test_finance_domain_adapter_implements_interface():
    """Real adapter for finance domain must produce valid DomainSnapshot."""
    from abraxas.adapters.domain_data import DomainSnapshot
    from abraxas.adapters.finance_domain_adapter import FinanceDomainAdapter
    adapter = FinanceDomainAdapter(domain="finance")
    snap = adapter.fetch_current_state()
    assert isinstance(snap, DomainSnapshot)
    assert snap.domain == "finance"
    assert snap.source == "finance-adapter"

def test_main_uses_real_adapters_for_all_when_not_mock():
    """When --mock false, all domains (politics/media/finance) must use real adapters."""
    from scripts.run_production_pipeline import main
    with patch("argparse.ArgumentParser.parse_args") as mock_parse:
        mock_parse.return_value = type("Args", (), {"domains": ["politics", "media", "finance"], "mock": False, "output": "/tmp", "interval": 1})()
        with patch("scripts.run_production_pipeline.ProductionPipeline"), \
             patch("scripts.run_production_pipeline.PoliticsDomainAdapter") as p, \
             patch("scripts.run_production_pipeline.MediaDomainAdapter") as m, \
             patch("scripts.run_production_pipeline.FinanceDomainAdapter") as f:
            main()
            p.assert_called_once_with(domain="politics")
            m.assert_called_once_with(domain="media")
            f.assert_called_once_with(domain="finance")


def test_postgresql_domain_adapter_implements_interface():
    """Real adapter for postgresql domain must produce valid DomainSnapshot."""
    from abraxas.adapters.domain_data import DomainSnapshot
    from abraxas.adapters.postgresql_domain_adapter import PostgreSQLDomainAdapter
    adapter = PostgreSQLDomainAdapter(dsn="dsn", domain_name="postgresql")
    snap = adapter.fetch_current_state()
    assert isinstance(snap, DomainSnapshot)
    assert snap.domain == "postgresql"
    assert len(snap.tokens) >= 1
    assert snap.source == "postgresql"


def test_pipeline_dispatches_to_planned_stub_engines():
    """ProductionPipeline must dispatch to ALL 5 planned stub engines."""
    from scripts.run_production_pipeline import ProductionPipeline
    from abraxas.adapters.politics_domain_adapter import PoliticsDomainAdapter
    import tempfile
    adapters = {"politics": PoliticsDomainAdapter(domain="politics")}
    with tempfile.TemporaryDirectory() as td:
        pipeline = ProductionPipeline(adapters, output_dir=td)
        result = pipeline.run_cycle()
        assert hasattr(pipeline, "_dispatch_to_engines")
        eng = result.get("engine_evidence", [])
        engines = [e.get("engine") for e in eng]
        expected = {"resonance", "chronos", "aether", "semion", "hyperlex"}
        found = set(engines)
        missing = expected - found
        assert not missing, f"missing engine dispatch: {missing}; got {engines}"


def test_oracle_envelope_includes_engine_evidence():
    """_build_oracle_envelope must accept engine_evidence and embed it in oracle_signal."""
    from scripts.run_production_pipeline import ProductionPipeline
    from abraxas.adapters.politics_domain_adapter import PoliticsDomainAdapter
    import tempfile
    adapters = {"politics": PoliticsDomainAdapter(domain="politics")}
    with tempfile.TemporaryDirectory() as td:
        pipeline = ProductionPipeline(adapters, output_dir=td)
        result = pipeline.run_cycle()
        # Verify the method accepts engine_evidence by checking the signature
        import inspect
        sig = inspect.signature(pipeline._build_oracle_envelope)
        params = list(sig.parameters.keys())
        assert "engine_evidence" in params, (
            f"_build_oracle_envelope must accept engine_evidence; got {params}"
        )
        # Verify engine_evidence reaches oracle output via envelope
        oracle_bundle = result.get("oracle_bundle", {})
        oracle_envelope = result.get("oracle_envelope", {})
        oracle_signal = oracle_envelope.get("oracle_signal", {})
        eng_ev = oracle_signal.get("engine_evidence")
        assert eng_ev is not None, (
            f"oracle_signal must contain engine_evidence; got keys: {list(oracle_signal.keys())}"
        )
        assert isinstance(eng_ev, list), f"engine_evidence must be a list; got {type(eng_ev)}"
        assert len(eng_ev) >= 1, f"engine_evidence must have entries; got {len(eng_ev)}"
