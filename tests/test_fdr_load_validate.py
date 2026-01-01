"""
Tests for FDR load + validation.
"""

import pytest

from abraxas.forecast.decomposition.registry import load_fdr, match_components


def test_fdr_load_validate():
    registry = load_fdr("tests/fixtures/fdr/sample_fdr.yaml")

    assert registry.version == "0.1"

    synth_matches = match_components(
        registry, topic_key="deepfake_pollution", horizon="H5Y", domain="FORECAST"
    )
    assert [c.component_id for c in synth_matches] == ["FDR_SYNTH_COST_CURVE"]

    slang_matches = match_components(
        registry, topic_key="term_cluster:xyz", horizon="H30D", domain="FORECAST"
    )
    assert [c.component_id for c in slang_matches] == ["FDR_SLANG_HANDLE_EMERGENCE"]


def test_fdr_invalid_wildcard():
    with pytest.raises(ValueError):
        load_fdr("tests/fixtures/fdr/invalid_wildcard.yaml")
