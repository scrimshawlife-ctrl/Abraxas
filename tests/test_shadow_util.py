"""
Tests for shadow detector utility helpers.

Verifies ok(), not_computable(), err() create proper ShadowResult objects.
"""

import pytest

from abraxas.detectors.shadow.util import ok, not_computable, err
from abraxas.detectors.shadow.types import ShadowResult


class TestOkHelper:
    """Test ok() helper function."""

    def test_creates_shadow_result(self):
        """Test that ok() returns a ShadowResult."""
        result = ok({"score": 0.5})
        assert isinstance(result, ShadowResult)

    def test_status_is_ok(self):
        """Test that status is 'ok'."""
        result = ok("value")
        assert result.status == "ok"

    def test_value_is_set(self):
        """Test that value is set correctly."""
        result = ok({"score": 0.75, "confidence": 0.9})
        assert result.value == {"score": 0.75, "confidence": 0.9}

    def test_missing_is_empty(self):
        """Test that missing is empty list."""
        result = ok("value")
        assert result.missing == []

    def test_error_is_none(self):
        """Test that error is None."""
        result = ok("value")
        assert result.error is None

    def test_provenance_default_empty(self):
        """Test that provenance defaults to empty dict."""
        result = ok("value")
        assert result.provenance == {}

    def test_provenance_is_set(self):
        """Test that provenance is set correctly."""
        result = ok("value", provenance={"version": "1.0"})
        assert result.provenance == {"version": "1.0"}

    def test_accepts_none_value(self):
        """Test that None is a valid value."""
        result = ok(None)
        assert result.status == "ok"
        assert result.value is None


class TestNotComputableHelper:
    """Test not_computable() helper function."""

    def test_creates_shadow_result(self):
        """Test that not_computable() returns a ShadowResult."""
        result = not_computable(["text"])
        assert isinstance(result, ShadowResult)

    def test_status_is_not_computable(self):
        """Test that status is 'not_computable'."""
        result = not_computable(["text"])
        assert result.status == "not_computable"

    def test_missing_is_set(self):
        """Test that missing is set correctly."""
        result = not_computable(["text", "tokens"])
        assert result.missing == ["text", "tokens"]

    def test_value_is_none(self):
        """Test that value is None."""
        result = not_computable(["text"])
        assert result.value is None

    def test_error_is_none(self):
        """Test that error is None."""
        result = not_computable(["text"])
        assert result.error is None

    def test_provenance_default_empty(self):
        """Test that provenance defaults to empty dict."""
        result = not_computable(["text"])
        assert result.provenance == {}

    def test_provenance_is_set(self):
        """Test that provenance is set correctly."""
        result = not_computable(["text"], provenance={"reason": "validation"})
        assert result.provenance == {"reason": "validation"}

    def test_empty_missing_list(self):
        """Test that empty missing list is valid."""
        result = not_computable([])
        assert result.missing == []


class TestErrHelper:
    """Test err() helper function."""

    def test_creates_shadow_result(self):
        """Test that err() returns a ShadowResult."""
        result = err("Something failed")
        assert isinstance(result, ShadowResult)

    def test_status_is_error(self):
        """Test that status is 'error'."""
        result = err("Something failed")
        assert result.status == "error"

    def test_error_is_set(self):
        """Test that error message is set."""
        result = err("Division by zero")
        assert result.error == "Division by zero"

    def test_value_is_none(self):
        """Test that value is None."""
        result = err("Something failed")
        assert result.value is None

    def test_missing_is_empty(self):
        """Test that missing is empty list."""
        result = err("Something failed")
        assert result.missing == []

    def test_provenance_default_empty(self):
        """Test that provenance defaults to empty dict."""
        result = err("Something failed")
        assert result.provenance == {}

    def test_provenance_is_set(self):
        """Test that provenance is set correctly."""
        result = err("fail", provenance={"stage": "parsing"})
        assert result.provenance == {"stage": "parsing"}


class TestResultImmutability:
    """Test that ShadowResult is immutable (frozen)."""

    def test_ok_result_is_frozen(self):
        """Test that ok() result is frozen."""
        result = ok("value")
        with pytest.raises(AttributeError):
            result.status = "error"

    def test_not_computable_result_is_frozen(self):
        """Test that not_computable() result is frozen."""
        result = not_computable(["x"])
        with pytest.raises(AttributeError):
            result.missing = ["y"]

    def test_err_result_is_frozen(self):
        """Test that err() result is frozen."""
        result = err("fail")
        with pytest.raises(AttributeError):
            result.error = "changed"


class TestDetectorUsagePattern:
    """Test the canonical usage pattern for detectors."""

    def test_missing_input_pattern(self):
        """Test the canonical pattern for missing inputs."""

        def run_shadow(ctx):
            text = ctx.get("text")
            if text is None:
                return not_computable(["text"])
            return ok({"length": len(text)})

        # Missing text
        result = run_shadow({})
        assert result.status == "not_computable"
        assert result.missing == ["text"]

        # Has text
        result = run_shadow({"text": "hello world"})
        assert result.status == "ok"
        assert result.value == {"length": 11}

    def test_multiple_missing_inputs_pattern(self):
        """Test pattern for multiple required inputs."""

        def run_shadow(ctx):
            missing = []
            if "text" not in ctx:
                missing.append("text")
            if "tokens" not in ctx:
                missing.append("tokens")
            if missing:
                return not_computable(missing)
            return ok({"text_len": len(ctx["text"]), "token_count": len(ctx["tokens"])})

        # All missing
        result = run_shadow({})
        assert result.status == "not_computable"
        assert result.missing == ["text", "tokens"]

        # Partial missing
        result = run_shadow({"text": "hello"})
        assert result.status == "not_computable"
        assert result.missing == ["tokens"]

        # All present
        result = run_shadow({"text": "hello", "tokens": ["hello"]})
        assert result.status == "ok"

    def test_error_pattern(self):
        """Test the canonical pattern for errors."""

        def run_shadow(ctx):
            text = ctx.get("text")
            if text is None:
                return not_computable(["text"])
            if len(text) == 0:
                return err("Empty text not allowed")
            return ok({"length": len(text)})

        # Empty text
        result = run_shadow({"text": ""})
        assert result.status == "error"
        assert result.error == "Empty text not allowed"


class TestBackwardCompatibility:
    """Test backward compatibility with normalize.py exports."""

    def test_import_from_normalize(self):
        """Test that helpers can still be imported from normalize.py."""
        from abraxas.detectors.shadow.normalize import ok, not_computable, error

        result = ok("value")
        assert result.status == "ok"

        result = not_computable(["x"])
        assert result.status == "not_computable"

        result = error("fail")
        assert result.status == "error"

    def test_import_from_package(self):
        """Test that helpers can be imported from package root."""
        from abraxas.detectors.shadow import ok, not_computable, err, error

        assert ok("v").status == "ok"
        assert not_computable(["x"]).status == "not_computable"
        assert err("f").status == "error"
        assert error("f").status == "error"  # alias
