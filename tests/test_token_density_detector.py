"""
Tests for token_density detector — demonstrates the new util helper pattern.

This detector uses ok(), not_computable(), err() helpers and returns ShadowResult.
"""

import pytest
from dataclasses import asdict

from abraxas.detectors.shadow.token_density import run_token_density, DETECTOR_VERSION
from abraxas.detectors.shadow.types import ShadowResult


class TestTokenDensityDetector:
    """Test the token density detector."""

    def test_returns_shadow_result(self):
        """Test that detector returns ShadowResult dataclass."""
        result = run_token_density({"text": "hello world"})
        assert isinstance(result, ShadowResult)

    def test_missing_text_returns_not_computable(self):
        """Test that missing text returns not_computable."""
        result = run_token_density({})

        assert result.status == "not_computable"
        assert result.missing == ["text"]
        assert result.value is None
        assert result.error is None

    def test_empty_text_returns_not_computable(self):
        """Test that empty text returns not_computable."""
        result = run_token_density({"text": ""})

        assert result.status == "not_computable"
        assert result.missing == ["text"]
        assert result.provenance.get("reason") == "empty_text"

    def test_whitespace_text_returns_not_computable(self):
        """Test that whitespace-only text returns not_computable."""
        result = run_token_density({"text": "   \t\n  "})

        assert result.status == "not_computable"
        assert result.missing == ["text"]

    def test_invalid_text_type_returns_error(self):
        """Test that non-string text returns error."""
        result = run_token_density({"text": 12345})

        assert result.status == "error"
        assert "Expected text to be str" in result.error

    def test_valid_text_returns_ok(self):
        """Test that valid text returns ok with metrics."""
        result = run_token_density({"text": "hello world test"})

        assert result.status == "ok"
        assert result.value is not None
        assert "tokens_per_100_chars" in result.value
        assert "unique_ratio" in result.value
        assert "avg_token_length" in result.value
        assert "token_count" in result.value
        assert "char_count" in result.value

    def test_metrics_are_correct(self):
        """Test that computed metrics are correct."""
        result = run_token_density({"text": "hello hello world"})

        assert result.status == "ok"
        value = result.value

        # 3 tokens, 2 unique
        assert value["token_count"] == 3
        assert value["unique_count"] == 2

        # unique_ratio = 2/3 ≈ 0.6667
        assert 0.66 < value["unique_ratio"] < 0.67

        # avg_token_length = (5+5+5)/3 = 5.0
        assert value["avg_token_length"] == 5.0

    def test_provenance_includes_version(self):
        """Test that provenance includes detector version."""
        result = run_token_density({"text": "hello"})

        assert result.status == "ok"
        assert result.provenance.get("version") == DETECTOR_VERSION

    def test_no_tokens_found(self):
        """Test text with no word tokens (punctuation only)."""
        result = run_token_density({"text": "!!! ??? ..."})

        assert result.status == "ok"
        assert result.value["token_count"] == 0
        assert result.value["unique_ratio"] == 0.0
        assert result.provenance.get("note") == "no_tokens_found"


class TestTokenDensityInRegistry:
    """Test that token_density is properly registered."""

    def test_in_registry_impl(self):
        """Test that token_density is in the registry."""
        from abraxas.detectors.shadow.registry_impl import get_detector_names

        names = get_detector_names()
        assert "token_density" in names

    def test_task_callable_works(self):
        """Test that the task callable works."""
        from abraxas.detectors.shadow.registry_impl import build_shadow_task_map

        tasks = build_shadow_task_map()
        assert "token_density" in tasks

        # Call the task
        result = tasks["token_density"]({"text": "hello world"})

        # Result should be a dict (asdict of ShadowResult)
        assert isinstance(result, dict)
        assert result["status"] == "ok"
        assert result["value"]["token_count"] == 2

    def test_integrates_with_tick(self):
        """Test that token_density runs in abraxas_tick."""
        import tempfile
        import json
        from abraxas.runtime import abraxas_tick

        with tempfile.TemporaryDirectory() as tmpdir:
            result = abraxas_tick(
                tick=0,
                run_id="TEST-TD-001",
                mode="test",
                context={
                    "text": "test text for token density detector",
                    "domain": "test",
                },
                artifacts_dir=tmpdir,
            )

            # Should have shadow:token_density in results
            assert "shadow:token_density" in result["results"]

            td_result = result["results"]["shadow:token_density"]
            td_value = td_result["value"]

            # Output should be normalized canonical shape
            assert td_value["status"] == "ok"
            assert "token_count" in td_value["value"]
