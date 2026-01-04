"""
Tests for shadow output normalization.

Verifies that arbitrary detector outputs are normalized to canonical shape:
- status: "ok" | "not_computable" | "error"
- value: payload (if ok)
- missing: list of missing inputs (if not_computable)
- error: string (if error)
- provenance: deterministic metadata
"""

import tempfile
import json

import pytest

from abraxas.detectors.shadow.normalize import (
    normalize_shadow_output,
    wrap_shadow_task,
    not_computable,
    ok,
    error,
)
from abraxas.detectors.shadow.types import ShadowResult
from abraxas.runtime import abraxas_tick


class TestNormalizeShadowOutput:
    """Test normalize_shadow_output() function."""

    def test_accepts_shadow_result(self):
        """Test that ShadowResult dataclass is normalized correctly."""
        out = ShadowResult(
            status="not_computable",
            value=None,
            missing=["text", "tokens"],
            error=None,
            provenance={"detector_version": "1.0"},
        )
        d = normalize_shadow_output(name="test_detector", out=out, provenance={"run_id": "R1"})

        assert d["status"] == "not_computable"
        assert d["missing"] == ["text", "tokens"]
        assert d["value"] is None
        assert d["error"] is None
        assert "provenance" in d
        assert d["provenance"]["detector"] == "test_detector"
        assert d["provenance"]["run_id"] == "R1"
        # Original provenance merged
        assert d["provenance"]["detector_version"] == "1.0"

    def test_accepts_dict_with_status(self):
        """Test that dict with status key is respected."""
        out = {
            "status": "error",
            "error": "Division by zero",
            "value": None,
        }
        d = normalize_shadow_output(name="test_detector", out=out)

        assert d["status"] == "error"
        assert d["error"] == "Division by zero"
        assert d["value"] is None
        assert d["missing"] == []
        assert d["provenance"]["detector"] == "test_detector"

    def test_arbitrary_payload_becomes_ok(self):
        """Test that arbitrary output becomes status=ok with value."""
        out = {"score": 0.75, "confidence": 0.9}
        d = normalize_shadow_output(name="test_detector", out=out)

        assert d["status"] == "ok"
        assert d["value"] == {"score": 0.75, "confidence": 0.9}
        assert d["missing"] == []
        assert d["error"] is None

    def test_string_payload_becomes_ok(self):
        """Test that string output becomes status=ok."""
        out = "some string result"
        d = normalize_shadow_output(name="test_detector", out=out)

        assert d["status"] == "ok"
        assert d["value"] == "some string result"

    def test_none_payload_becomes_ok(self):
        """Test that None output becomes status=ok with None value."""
        d = normalize_shadow_output(name="test_detector", out=None)

        assert d["status"] == "ok"
        assert d["value"] is None

    def test_provenance_is_deterministic(self):
        """Test that provenance keys are sorted for determinism."""
        d = normalize_shadow_output(
            name="test",
            out="payload",
            provenance={"z": 1, "a": 2, "m": 3},
        )
        # Keys should be sorted in provenance
        keys = list(d["provenance"].keys())
        # detector comes first, then sorted additional keys
        assert keys[0] == "detector"


class TestWrapShadowTask:
    """Test wrap_shadow_task() wrapper function."""

    def test_converts_arbitrary_payload_to_ok(self):
        """Test that arbitrary return becomes ok."""

        def fn(ctx):
            return {"hello": "world"}

        wrapped = wrap_shadow_task("demo", fn)
        d = wrapped({})

        assert d["status"] == "ok"
        assert d["value"] == {"hello": "world"}
        assert d["provenance"]["wrapper"] == "shadow.normalize.v0"
        assert d["provenance"]["detector"] == "demo"

    def test_catches_exceptions(self):
        """Test that exceptions become error status."""

        def fn(ctx):
            raise ValueError("boom")

        wrapped = wrap_shadow_task("demo", fn)
        d = wrapped({})

        assert d["status"] == "error"
        assert "ValueError" in d["error"]
        assert "boom" in d["error"]
        assert d["provenance"]["detector"] == "demo"

    def test_preserves_shadow_result(self):
        """Test that ShadowResult is preserved through wrapper."""

        def fn(ctx):
            return ShadowResult(
                status="not_computable",
                missing=["required_key"],
            )

        wrapped = wrap_shadow_task("demo", fn)
        d = wrapped({})

        assert d["status"] == "not_computable"
        assert d["missing"] == ["required_key"]

    def test_preserves_dict_status(self):
        """Test that dict with status is preserved."""

        def fn(ctx):
            return {"status": "not_computable", "missing": ["x", "y"]}

        wrapped = wrap_shadow_task("demo", fn)
        d = wrapped({})

        assert d["status"] == "not_computable"
        assert d["missing"] == ["x", "y"]


class TestHelperFunctions:
    """Test helper functions for detector authors."""

    def test_not_computable_helper(self):
        """Test not_computable() helper."""
        result = not_computable(["text", "tokens"])

        assert isinstance(result, ShadowResult)
        assert result.status == "not_computable"
        assert result.missing == ["text", "tokens"]
        assert result.value is None
        assert result.error is None

    def test_not_computable_with_provenance(self):
        """Test not_computable() with provenance."""
        result = not_computable(["x"], provenance={"version": "1.0"})

        assert result.status == "not_computable"
        assert result.provenance == {"version": "1.0"}

    def test_ok_helper(self):
        """Test ok() helper."""
        result = ok({"score": 0.5})

        assert isinstance(result, ShadowResult)
        assert result.status == "ok"
        assert result.value == {"score": 0.5}
        assert result.missing == []
        assert result.error is None

    def test_ok_with_provenance(self):
        """Test ok() with provenance."""
        result = ok("payload", provenance={"run": "R1"})

        assert result.status == "ok"
        assert result.provenance == {"run": "R1"}

    def test_error_helper(self):
        """Test error() helper."""
        result = error("Something went wrong")

        assert isinstance(result, ShadowResult)
        assert result.status == "error"
        assert result.error == "Something went wrong"
        assert result.value is None
        assert result.missing == []

    def test_error_with_provenance(self):
        """Test error() with provenance."""
        result = error("fail", provenance={"stage": "validation"})

        assert result.status == "error"
        assert result.provenance == {"stage": "validation"}


class TestTickIntegration:
    """Test that shadow tasks are normalized in abraxas_tick()."""

    def test_shadow_tasks_are_normalized_in_tick(self):
        """Test that shadow task outputs are normalized in tick execution."""

        def run_signal(ctx):
            return {"signal": "ok"}

        def run_compress(ctx):
            return {"compress": "ok"}

        def run_overlay(ctx):
            return {"overlay": "ok"}

        # Shadow task returning arbitrary dict (no status)
        def shadow_arbitrary(ctx):
            return {"raw": "data", "score": 42}

        # Shadow task returning explicit status
        def shadow_not_computable(ctx):
            return {"status": "not_computable", "missing": ["required_field"]}

        with tempfile.TemporaryDirectory() as tmpdir:
            result = abraxas_tick(
                tick=0,
                run_id="TEST-NORM-001",
                mode="test",
                context={},
                artifacts_dir=tmpdir,
                run_signal=run_signal,
                run_compress=run_compress,
                run_overlay=run_overlay,
                run_shadow_tasks={
                    "arbitrary": shadow_arbitrary,
                    "not_computable": shadow_not_computable,
                },
            )

            # Verify shadow tasks executed
            assert "shadow:arbitrary" in result["results"]
            assert "shadow:not_computable" in result["results"]

            # Verify outputs are normalized (results contain TaskResult with value field)
            arbitrary_result = result["results"]["shadow:arbitrary"]
            nc_result = result["results"]["shadow:not_computable"]

            # TaskResult has 'value' field containing the normalized result
            arbitrary_output = arbitrary_result["value"]
            nc_output = nc_result["value"]

            # Arbitrary dict should become ok
            assert arbitrary_output["status"] == "ok"
            assert arbitrary_output["value"] == {"raw": "data", "score": 42}
            assert "provenance" in arbitrary_output

            # Explicit status should be preserved
            assert nc_output["status"] == "not_computable"
            assert nc_output["missing"] == ["required_field"]

    def test_shadow_exception_becomes_error_status(self):
        """Test that shadow task exceptions become error status."""

        def run_signal(ctx):
            return {"signal": "ok"}

        def run_compress(ctx):
            return {"compress": "ok"}

        def run_overlay(ctx):
            return {"overlay": "ok"}

        def shadow_raises(ctx):
            raise RuntimeError("Detector crashed")

        with tempfile.TemporaryDirectory() as tmpdir:
            result = abraxas_tick(
                tick=0,
                run_id="TEST-ERR-001",
                mode="test",
                context={},
                artifacts_dir=tmpdir,
                run_signal=run_signal,
                run_compress=run_compress,
                run_overlay=run_overlay,
                run_shadow_tasks={"raises": shadow_raises},
            )

            # Shadow task should have executed (not crashed the tick)
            assert "shadow:raises" in result["results"]

            raises_output = result["results"]["shadow:raises"]["value"]
            assert raises_output["status"] == "error"
            assert "RuntimeError" in raises_output["error"]
            assert "Detector crashed" in raises_output["error"]


class TestDeterminism:
    """Test that normalization is deterministic."""

    def test_normalize_is_deterministic(self):
        """Test that same input produces same output."""
        out = {"score": 0.5, "data": [1, 2, 3]}

        d1 = normalize_shadow_output(name="test", out=out, provenance={"run": "R1"})
        d2 = normalize_shadow_output(name="test", out=out, provenance={"run": "R1"})

        assert d1 == d2

    def test_wrapped_task_is_deterministic(self):
        """Test that wrapped task produces same output for same input."""

        def fn(ctx):
            return {"value": ctx.get("x", 0) * 2}

        wrapped = wrap_shadow_task("test", fn)

        d1 = wrapped({"x": 5})
        d2 = wrapped({"x": 5})

        assert d1 == d2
        assert d1["value"] == {"value": 10}
