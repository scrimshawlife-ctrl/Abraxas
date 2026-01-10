"""
Tests for viz_resolve module.

Verifies:
- TrendPack loading and validation
- ResultsPack loading and validation
- Event result resolution via result_ref
- Full resolve_trendpack_events flow
"""

import json
import tempfile
from pathlib import Path

import pytest

from abraxas.runtime.viz_resolve import (
    load_trendpack,
    load_resultspack,
    resolve_event_result,
    resolve_trendpack_events,
    get_event_result_by_task,
    clear_resultspack_cache,
)
from abraxas.runtime.tick import abraxas_tick


class TestLoadTrendpack:
    """Test load_trendpack() function."""

    def test_loads_valid_trendpack(self):
        """Test loading a valid TrendPack."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"version": "0.1", "timeline": []}, f)
            f.flush()

            tp = load_trendpack(f.name)
            assert tp["version"] == "0.1"

    def test_rejects_invalid_schema(self):
        """Test that invalid schema raises ValueError."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"version": "9.9", "timeline": []}, f)
            f.flush()

            with pytest.raises(ValueError, match="Expected TrendPack.v0"):
                load_trendpack(f.name)


class TestLoadResultspack:
    """Test load_resultspack() function."""

    def test_loads_valid_resultspack(self):
        """Test loading a valid ResultsPack."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"schema": "ResultsPack.v0", "items": []}, f)
            f.flush()

            rp = load_resultspack(f.name)
            assert rp["schema"] == "ResultsPack.v0"

    def test_rejects_invalid_schema(self):
        """Test that invalid schema raises ValueError."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"schema": "WrongSchema", "items": []}, f)
            f.flush()

            with pytest.raises(ValueError, match="Expected ResultsPack.v0"):
                load_resultspack(f.name)


class TestResolveEventResult:
    """Test resolve_event_result() function."""

    def test_event_without_ref_returns_none_result(self):
        """Test that event without result_ref returns None result."""
        event = {"task": "test", "lane": "forecast", "meta": {}}
        resolved = resolve_event_result(event)

        assert resolved["event"] == event
        assert resolved["result"] is None
        assert resolved["ref"] is None

    def test_event_with_invalid_ref_returns_none_result(self):
        """Test that event with invalid ref schema returns None result."""
        event = {
            "task": "test",
            "lane": "forecast",
            "meta": {"result_ref": {"schema": "WrongSchema"}},
        }
        resolved = resolve_event_result(event)

        assert resolved["event"] == event
        assert resolved["result"] is None
        assert resolved["ref"] is None

    def test_event_with_missing_resultspack_returns_none_result(self):
        """Test graceful handling of missing ResultsPack file."""
        clear_resultspack_cache()
        event = {
            "task": "test",
            "lane": "forecast",
            "meta": {
                "result_ref": {
                    "schema": "ResultRef.v0",
                    "results_pack": "/nonexistent/path.json",
                    "task": "test",
                }
            },
        }
        resolved = resolve_event_result(event)

        assert resolved["event"] == event
        assert resolved["result"] is None
        assert resolved["ref"] is not None  # Ref exists but couldn't resolve


class TestResolveTrendpackEvents:
    """Test resolve_trendpack_events() with real tick output."""

    def test_resolves_events_from_tick(self):
        """Test resolving events from a real abraxas_tick output."""

        def run_signal(ctx):
            return {"signal": "ok"}

        def run_compress(ctx):
            return {"compress": "ok"}

        def run_overlay(ctx):
            return {"overlay": "ok"}

        with tempfile.TemporaryDirectory() as tmpdir:
            result = abraxas_tick(
                tick=0,
                run_id="viz-test",
                mode="test",
                context={},
                artifacts_dir=tmpdir,
                run_signal=run_signal,
                run_compress=run_compress,
                run_overlay=run_overlay,
            )

            tp_path = result["artifacts"]["trendpack"]
            resolved = resolve_trendpack_events(tp_path)

            # Should have at least 3 events (oracle tasks)
            assert len(resolved) >= 3

            # Each resolved entry should have the expected structure
            for r in resolved:
                assert "event" in r
                assert "result" in r
                assert "ref" in r

            # At least one should have a valid ref and result
            has_valid_resolution = any(
                r["ref"] is not None and r["result"] is not None
                for r in resolved
            )
            assert has_valid_resolution

    def test_limit_parameter(self):
        """Test that limit parameter restricts results."""

        def run_signal(ctx):
            return {"signal": "ok"}

        def run_compress(ctx):
            return {"compress": "ok"}

        def run_overlay(ctx):
            return {"overlay": "ok"}

        with tempfile.TemporaryDirectory() as tmpdir:
            result = abraxas_tick(
                tick=0,
                run_id="viz-limit",
                mode="test",
                context={},
                artifacts_dir=tmpdir,
                run_signal=run_signal,
                run_compress=run_compress,
                run_overlay=run_overlay,
            )

            tp_path = result["artifacts"]["trendpack"]

            # Get all events
            all_resolved = resolve_trendpack_events(tp_path)

            # Get limited events
            limited = resolve_trendpack_events(tp_path, limit=2)

            assert len(limited) == 2
            assert len(all_resolved) >= len(limited)


class TestGetEventResultByTask:
    """Test get_event_result_by_task() convenience function."""

    def test_finds_specific_task(self):
        """Test finding a specific task by name."""

        def run_signal(ctx):
            return {"signal": "found"}

        def run_compress(ctx):
            return {"compress": "ok"}

        def run_overlay(ctx):
            return {"overlay": "ok"}

        with tempfile.TemporaryDirectory() as tmpdir:
            result = abraxas_tick(
                tick=0,
                run_id="viz-task",
                mode="test",
                context={},
                artifacts_dir=tmpdir,
                run_signal=run_signal,
                run_compress=run_compress,
                run_overlay=run_overlay,
            )

            tp_path = result["artifacts"]["trendpack"]

            # Find oracle:signal task
            resolved = get_event_result_by_task(tp_path, "oracle:signal")

            assert resolved is not None
            assert resolved["event"]["task"] == "oracle:signal"
            assert resolved["result"] is not None
            assert resolved["result"]["value"]["signal"] == "found"

    def test_returns_none_for_nonexistent_task(self):
        """Test that nonexistent task returns None."""

        def run_signal(ctx):
            return {"signal": "ok"}

        def run_compress(ctx):
            return {"compress": "ok"}

        def run_overlay(ctx):
            return {"overlay": "ok"}

        with tempfile.TemporaryDirectory() as tmpdir:
            result = abraxas_tick(
                tick=0,
                run_id="viz-notfound",
                mode="test",
                context={},
                artifacts_dir=tmpdir,
                run_signal=run_signal,
                run_compress=run_compress,
                run_overlay=run_overlay,
            )

            tp_path = result["artifacts"]["trendpack"]

            # Try to find nonexistent task
            resolved = get_event_result_by_task(tp_path, "nonexistent:task")
            assert resolved is None


class TestWithShadowTasks:
    """Test resolution with shadow tasks (normalized outputs)."""

    def test_resolves_shadow_task_results(self):
        """Test that shadow task results are properly resolved."""

        def run_signal(ctx):
            return {"signal": "ok"}

        def run_compress(ctx):
            return {"compress": "ok"}

        def run_overlay(ctx):
            return {"overlay": "ok"}

        def shadow_test(ctx):
            return {"status": "ok", "value": {"shadow_data": 42}}

        with tempfile.TemporaryDirectory() as tmpdir:
            result = abraxas_tick(
                tick=0,
                run_id="viz-shadow",
                mode="test",
                context={},
                artifacts_dir=tmpdir,
                run_signal=run_signal,
                run_compress=run_compress,
                run_overlay=run_overlay,
                run_shadow_tasks={"test": shadow_test},
            )

            tp_path = result["artifacts"]["trendpack"]

            # Find shadow task
            resolved = get_event_result_by_task(tp_path, "shadow:test")

            assert resolved is not None
            assert resolved["event"]["task"] == "shadow:test"
            assert resolved["event"]["lane"] == "shadow"
            assert resolved["result"] is not None


class TestIntegrationWithNativeBindings:
    """Test full integration with native pipeline bindings."""

    def test_viz_resolve_with_native_bindings(self):
        """Test resolving events when using native pipeline bindings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = abraxas_tick(
                tick=0,
                run_id="viz-native",
                mode="sandbox",
                context={"tokens": ["test"]},
                artifacts_dir=tmpdir,
                bindings=None,  # Use native resolution
            )

            tp_path = result["artifacts"]["trendpack"]
            resolved = resolve_trendpack_events(tp_path)

            # Should have events from all lanes
            forecast_events = [r for r in resolved if r["event"]["lane"] == "forecast"]
            shadow_events = [r for r in resolved if r["event"]["lane"] == "shadow"]

            assert len(forecast_events) >= 3  # oracle:signal, compress, overlay
            assert len(shadow_events) >= 1  # At least one shadow detector

            # Verify resolution worked
            for r in resolved:
                if r["ref"] is not None:
                    # If we have a ref, we should either have a result or a graceful None
                    assert "result" in r
