"""
Tests for abraxas.runtime.pipeline_bindings - Native Pipeline Resolution.

Tests that the resolver correctly finds and binds the Oracle pipeline
functions and shadow tasks from canonical registries.
"""

import tempfile
from pathlib import Path
import json

import pytest

from abraxas.runtime.pipeline_bindings import (
    PipelineBindings,
    resolve_pipeline_bindings,
)
from abraxas.runtime import abraxas_tick


class TestResolvePipelineBindings:
    """Test the pipeline bindings resolver."""

    def test_resolve_succeeds(self):
        """Test that resolve_pipeline_bindings() succeeds with canonical registries."""
        bindings = resolve_pipeline_bindings()

        assert isinstance(bindings, PipelineBindings)
        assert callable(bindings.run_signal)
        assert callable(bindings.run_compress)
        assert callable(bindings.run_overlay)
        assert isinstance(bindings.shadow_tasks, dict)
        assert isinstance(bindings.provenance, dict)

    def test_bindings_are_frozen(self):
        """Test that PipelineBindings is immutable (frozen dataclass)."""
        bindings = resolve_pipeline_bindings()

        with pytest.raises(AttributeError):
            bindings.run_signal = lambda x: x

    def test_provenance_structure(self):
        """Test that provenance contains expected fields."""
        bindings = resolve_pipeline_bindings()

        assert "bindings" in bindings.provenance
        assert bindings.provenance["bindings"] == "PipelineBindings.v1"
        assert "oracle" in bindings.provenance
        assert "shadow" in bindings.provenance

        oracle_prov = bindings.provenance["oracle"]
        assert "signal" in oracle_prov
        assert "compress" in oracle_prov
        assert "overlay" in oracle_prov

        shadow_prov = bindings.provenance["shadow"]
        assert "provider" in shadow_prov
        assert "task_count" in shadow_prov
        assert "task_names" in shadow_prov

    def test_shadow_tasks_populated(self):
        """Test that shadow tasks are discovered from the repo."""
        bindings = resolve_pipeline_bindings()

        # Should find the shadow detectors
        assert len(bindings.shadow_tasks) > 0
        # All tasks should be callable
        for name, fn in bindings.shadow_tasks.items():
            assert callable(fn), f"Shadow task {name} is not callable"

    def test_provenance_shows_canonical_registry_source(self):
        """Test that provenance shows the canonical registry as source."""
        bindings = resolve_pipeline_bindings()

        oracle_prov = bindings.provenance["oracle"]
        # Should show canonical registry paths
        assert oracle_prov["signal"] == "abraxas.oracle.registry:run_signal"
        assert oracle_prov["compress"] == "abraxas.oracle.registry:run_compress"
        assert oracle_prov["overlay"] == "abraxas.oracle.registry:run_overlay"

        shadow_prov = bindings.provenance["shadow"]
        assert shadow_prov["provider"] == "abraxas.detectors.shadow.registry:get_shadow_tasks"


class TestPipelineFunctionExecution:
    """Test that the resolved pipeline functions execute correctly."""

    def test_run_signal_executes(self):
        """Test that run_signal executes with context."""
        bindings = resolve_pipeline_bindings()

        ctx = {
            "observations": ["test observation one", "test observation two"],
            "domain": "test",
        }
        result = bindings.run_signal(ctx)

        assert isinstance(result, dict)
        assert result.get("status") == "ok"
        assert "signal" in result

    def test_run_compress_executes(self):
        """Test that run_compress executes after signal."""
        bindings = resolve_pipeline_bindings()

        ctx = {
            "observations": ["test observation"],
            "tokens": ["test", "observation"],
            "domain": "test",
            "run_id": "test-run",
        }
        # Run signal first to populate ctx
        bindings.run_signal(ctx)
        result = bindings.run_compress(ctx)

        assert isinstance(result, dict)
        assert result.get("status") == "ok"
        assert "compression" in result

    def test_run_overlay_executes(self):
        """Test that run_overlay executes after compression."""
        bindings = resolve_pipeline_bindings()

        ctx = {
            "observations": ["test observation"],
            "tokens": ["test", "observation"],
            "domain": "test",
            "run_id": "test-run",
        }
        # Run signal and compress first
        bindings.run_signal(ctx)
        bindings.run_compress(ctx)
        result = bindings.run_overlay(ctx)

        assert isinstance(result, dict)
        assert result.get("status") == "ok"
        assert "forecast" in result

    def test_shadow_task_executes(self):
        """Test that shadow tasks execute with context."""
        bindings = resolve_pipeline_bindings()

        if not bindings.shadow_tasks:
            pytest.skip("No shadow tasks available")

        ctx = {
            "text": "Test text for shadow detection",
            "reference_texts": ["Reference corpus text"],
        }

        for name, fn in bindings.shadow_tasks.items():
            result = fn(ctx)
            assert isinstance(result, dict), f"Shadow task {name} didn't return dict"


class TestAbraxasTickWithNativeBindings:
    """Test abraxas_tick() with native pipeline bindings."""

    def test_tick_with_auto_resolved_bindings(self):
        """Test that abraxas_tick() auto-resolves bindings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # No bindings or legacy params provided - should auto-resolve
            result = abraxas_tick(
                tick=0,
                run_id="TEST-NATIVE-001",
                mode="test",
                context={
                    "observations": ["test observation"],
                    "domain": "test",
                    "run_id": "TEST-NATIVE-001",
                },
                artifacts_dir=tmpdir,
            )

            # Verify result structure
            assert result["tick"] == 0
            assert result["run_id"] == "TEST-NATIVE-001"
            assert "artifacts" in result
            assert "trendpack" in result["artifacts"]

            # Verify TrendPack was written with pipeline_bindings provenance
            trendpack_path = result["artifacts"]["trendpack"]
            with open(trendpack_path) as f:
                trendpack = json.load(f)

            assert "pipeline_bindings" in trendpack["provenance"]
            prov = trendpack["provenance"]["pipeline_bindings"]
            assert prov["bindings"] == "PipelineBindings.v1"
            assert "oracle" in prov
            assert "shadow" in prov

    def test_tick_with_explicit_bindings(self):
        """Test that abraxas_tick() uses explicitly provided bindings."""
        bindings = resolve_pipeline_bindings()

        with tempfile.TemporaryDirectory() as tmpdir:
            result = abraxas_tick(
                tick=0,
                run_id="TEST-EXPLICIT-001",
                mode="test",
                context={
                    "observations": ["test observation"],
                    "domain": "test",
                    "run_id": "TEST-EXPLICIT-001",
                },
                artifacts_dir=tmpdir,
                bindings=bindings,
            )

            assert result["tick"] == 0
            assert result["run_id"] == "TEST-EXPLICIT-001"

    def test_tick_with_legacy_params_overrides_bindings(self):
        """Test that legacy params override bindings (backward compatibility)."""
        call_order = []

        def run_signal(ctx):
            call_order.append("signal")
            return {"signal": "legacy"}

        def run_compress(ctx):
            call_order.append("compress")
            return {"compress": "legacy"}

        def run_overlay(ctx):
            call_order.append("overlay")
            return {"overlay": "legacy"}

        with tempfile.TemporaryDirectory() as tmpdir:
            result = abraxas_tick(
                tick=0,
                run_id="TEST-LEGACY-001",
                mode="test",
                context={},
                artifacts_dir=tmpdir,
                run_signal=run_signal,
                run_compress=run_compress,
                run_overlay=run_overlay,
            )

            # Legacy functions should have been called
            assert call_order == ["signal", "compress", "overlay"]

            # Verify provenance shows legacy mode
            trendpack_path = result["artifacts"]["trendpack"]
            with open(trendpack_path) as f:
                trendpack = json.load(f)

            prov = trendpack["provenance"]["pipeline_bindings"]
            assert prov["bindings"] == "legacy_explicit"

    def test_tick_includes_shadow_tasks_from_bindings(self):
        """Test that tick includes shadow tasks when using native bindings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = abraxas_tick(
                tick=0,
                run_id="TEST-SHADOW-001",
                mode="test",
                context={
                    "text": "Test text for shadow analysis",
                    "domain": "test",
                    "run_id": "TEST-SHADOW-001",
                },
                artifacts_dir=tmpdir,
            )

            # Verify TrendPack includes shadow events
            trendpack_path = result["artifacts"]["trendpack"]
            with open(trendpack_path) as f:
                trendpack = json.load(f)

            # Should have shadow events (if shadow detectors are present)
            shadow_events = trendpack["stats"]["shadow_events"]
            # Note: shadow events count depends on available detectors
            # At minimum, we verify the structure is correct
            assert isinstance(shadow_events, int)


class TestDeterminism:
    """Test that pipeline resolution is deterministic."""

    def test_resolve_is_deterministic(self):
        """Test that multiple resolves produce identical bindings."""
        bindings1 = resolve_pipeline_bindings()
        bindings2 = resolve_pipeline_bindings()

        # Provenance should be identical (same sources found)
        assert bindings1.provenance == bindings2.provenance

        # Same shadow task names
        assert sorted(bindings1.shadow_tasks.keys()) == sorted(bindings2.shadow_tasks.keys())

    def test_shadow_task_order_is_stable(self):
        """Test that shadow tasks are always in the same order."""
        bindings1 = resolve_pipeline_bindings()
        bindings2 = resolve_pipeline_bindings()

        # Task names in provenance should be sorted
        names1 = bindings1.provenance["shadow"]["task_names"]
        names2 = bindings2.provenance["shadow"]["task_names"]

        assert names1 == names2
        assert names1 == sorted(names1)  # Should be sorted


class TestCanonicalRegistryImports:
    """Test that canonical registry imports work correctly."""

    def test_oracle_registry_direct_import(self):
        """Test that oracle registry can be imported directly."""
        from abraxas.oracle import registry as oracle_registry

        assert callable(oracle_registry.run_signal)
        assert callable(oracle_registry.run_compress)
        assert callable(oracle_registry.run_overlay)

    def test_shadow_registry_direct_import(self):
        """Test that shadow registry can be imported directly."""
        from abraxas.detectors.shadow import registry as shadow_registry

        assert callable(shadow_registry.get_shadow_tasks)

        tasks = shadow_registry.get_shadow_tasks({})
        assert isinstance(tasks, dict)

    def test_shadow_registry_impl_direct_import(self):
        """Test that shadow registry_impl can be imported directly."""
        from abraxas.detectors.shadow.registry_impl import build_shadow_task_map, get_detector_names

        tasks = build_shadow_task_map()
        assert isinstance(tasks, dict)
        assert len(tasks) > 0

        names = get_detector_names()
        assert isinstance(names, list)
        assert names == sorted(names)  # Should be sorted
