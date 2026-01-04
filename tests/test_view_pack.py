"""
Tests for ViewPack.v0 artifact.

Verifies:
- ViewPack is emitted by abraxas_tick
- ViewPack contains correct schema and structure
- Aggregates are populated from TrendPack
- Resolved events are filtered correctly
"""

import json
import tempfile
from pathlib import Path

import pytest

from abraxas.runtime import abraxas_tick, build_view_pack


class TestTickEmitsViewPack:
    """Test that abraxas_tick() emits ViewPack artifact."""

    def test_tick_emits_viewpack(self):
        """Test that tick emits ViewPack artifact."""

        def run_signal(ctx):
            return {"signal": "ok"}

        def run_compress(ctx):
            return {"compress": "ok"}

        def run_overlay(ctx):
            return {"overlay": "ok"}

        with tempfile.TemporaryDirectory() as tmpdir:
            result = abraxas_tick(
                tick=0,
                run_id="vp-test",
                mode="test",
                context={},
                artifacts_dir=tmpdir,
                run_signal=run_signal,
                run_compress=run_compress,
                run_overlay=run_overlay,
            )

            # Verify ViewPack path in artifacts
            assert "viewpack" in result["artifacts"]
            assert "viewpack_sha256" in result["artifacts"]

            # Verify file exists
            vp_path = Path(result["artifacts"]["viewpack"])
            assert vp_path.exists()

            # Verify structure
            with open(vp_path) as f:
                vp = json.load(f)

            assert vp["schema"] == "ViewPack.v0"
            assert vp["run_id"] == "vp-test"
            assert vp["tick"] == 0
            assert vp["mode"] == "test"

    def test_viewpack_contains_aggregates(self):
        """Test that ViewPack contains aggregates from TrendPack."""

        def run_signal(ctx):
            return {"signal": "ok"}

        def run_compress(ctx):
            return {"compress": "ok"}

        def run_overlay(ctx):
            return {"overlay": "ok"}

        with tempfile.TemporaryDirectory() as tmpdir:
            result = abraxas_tick(
                tick=0,
                run_id="vp-agg",
                mode="test",
                context={},
                artifacts_dir=tmpdir,
                run_signal=run_signal,
                run_compress=run_compress,
                run_overlay=run_overlay,
            )

            vp_path = Path(result["artifacts"]["viewpack"])
            with open(vp_path) as f:
                vp = json.load(f)

            # Check aggregates structure
            assert "aggregates" in vp
            agg = vp["aggregates"]

            assert "stats" in agg
            assert "budget" in agg
            assert "error_count" in agg
            assert "skipped_count" in agg

            # Stats should have counts
            assert agg["stats"]["total_events"] >= 3

    def test_viewpack_contains_events(self):
        """Test that ViewPack contains events list."""

        def run_signal(ctx):
            return {"signal": "ok"}

        def run_compress(ctx):
            return {"compress": "ok"}

        def run_overlay(ctx):
            return {"overlay": "ok"}

        with tempfile.TemporaryDirectory() as tmpdir:
            result = abraxas_tick(
                tick=0,
                run_id="vp-events",
                mode="test",
                context={},
                artifacts_dir=tmpdir,
                run_signal=run_signal,
                run_compress=run_compress,
                run_overlay=run_overlay,
            )

            vp_path = Path(result["artifacts"]["viewpack"])
            with open(vp_path) as f:
                vp = json.load(f)

            # Check events list
            assert "events" in vp
            assert len(vp["events"]) >= 3

            # Events should have expected structure
            for ev in vp["events"]:
                assert "task" in ev
                assert "lane" in ev
                assert "status" in ev

    def test_viewpack_contains_resolved_filter_info(self):
        """Test that ViewPack contains resolved filter metadata."""

        def run_signal(ctx):
            return {"signal": "ok"}

        def run_compress(ctx):
            return {"compress": "ok"}

        def run_overlay(ctx):
            return {"overlay": "ok"}

        with tempfile.TemporaryDirectory() as tmpdir:
            result = abraxas_tick(
                tick=0,
                run_id="vp-filter",
                mode="test",
                context={},
                artifacts_dir=tmpdir,
                run_signal=run_signal,
                run_compress=run_compress,
                run_overlay=run_overlay,
            )

            vp_path = Path(result["artifacts"]["viewpack"])
            with open(vp_path) as f:
                vp = json.load(f)

            # Check resolved filter info
            assert "resolved_filter" in vp
            rf = vp["resolved_filter"]

            assert "limit" in rf
            assert "status_filter" in rf
            assert "actual_count" in rf


class TestViewPackWithErrors:
    """Test ViewPack behavior with error/skipped events."""

    def test_viewpack_resolves_errors(self):
        """Test that ViewPack resolves error events."""

        def run_signal(ctx):
            raise ValueError("Test error")

        def run_compress(ctx):
            return {"compress": "ok"}

        def run_overlay(ctx):
            return {"overlay": "ok"}

        with tempfile.TemporaryDirectory() as tmpdir:
            result = abraxas_tick(
                tick=0,
                run_id="vp-error",
                mode="test",
                context={},
                artifacts_dir=tmpdir,
                run_signal=run_signal,
                run_compress=run_compress,
                run_overlay=run_overlay,
            )

            vp_path = Path(result["artifacts"]["viewpack"])
            with open(vp_path) as f:
                vp = json.load(f)

            # Should have at least one error event
            assert vp["aggregates"]["error_count"] >= 1

            # Resolved list should contain error events (since we filter to errors/skipped)
            # Note: resolved is filtered to errors/skipped by default
            resolved = vp["resolved"]
            error_resolved = [
                r for r in resolved
                if r.get("event", {}).get("status") == "error"
            ]
            assert len(error_resolved) >= 1


class TestBuildViewPackDirectly:
    """Test build_view_pack() function directly."""

    def test_build_view_pack_with_no_filter(self):
        """Test building ViewPack without status filter."""

        def run_signal(ctx):
            return {"signal": "ok"}

        def run_compress(ctx):
            return {"compress": "ok"}

        def run_overlay(ctx):
            return {"overlay": "ok"}

        with tempfile.TemporaryDirectory() as tmpdir:
            result = abraxas_tick(
                tick=0,
                run_id="vp-nofilter",
                mode="test",
                context={},
                artifacts_dir=tmpdir,
                run_signal=run_signal,
                run_compress=run_compress,
                run_overlay=run_overlay,
            )

            tp_path = result["artifacts"]["trendpack"]

            # Build ViewPack with no status filter
            vp = build_view_pack(
                trendpack_path=tp_path,
                run_id="vp-nofilter",
                tick=0,
                mode="test",
                resolve_limit=50,
                resolve_only_status=None,  # No filter
                provenance={"test": True},
            )

            assert vp["schema"] == "ViewPack.v0"

            # Without filter, should resolve all events (up to limit)
            assert len(vp["resolved"]) >= 3

    def test_build_view_pack_with_limit(self):
        """Test that resolve_limit caps resolved events."""

        def run_signal(ctx):
            return {"signal": "ok"}

        def run_compress(ctx):
            return {"compress": "ok"}

        def run_overlay(ctx):
            return {"overlay": "ok"}

        with tempfile.TemporaryDirectory() as tmpdir:
            result = abraxas_tick(
                tick=0,
                run_id="vp-limit",
                mode="test",
                context={},
                artifacts_dir=tmpdir,
                run_signal=run_signal,
                run_compress=run_compress,
                run_overlay=run_overlay,
            )

            tp_path = result["artifacts"]["trendpack"]

            # Build ViewPack with small limit
            vp = build_view_pack(
                trendpack_path=tp_path,
                run_id="vp-limit",
                tick=0,
                mode="test",
                resolve_limit=2,
                resolve_only_status=None,
            )

            # Should respect limit
            assert len(vp["resolved"]) <= 2


class TestViewPackWithNativeBindings:
    """Test ViewPack with native pipeline bindings."""

    def test_viewpack_with_native_bindings(self):
        """Test ViewPack works with native pipeline bindings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = abraxas_tick(
                tick=0,
                run_id="vp-native",
                mode="sandbox",
                context={"tokens": ["test"]},
                artifacts_dir=tmpdir,
                bindings=None,  # Use native
            )

            vp_path = Path(result["artifacts"]["viewpack"])
            assert vp_path.exists()

            with open(vp_path) as f:
                vp = json.load(f)

            assert vp["schema"] == "ViewPack.v0"

            # Should have both forecast and shadow events
            forecast_events = [
                e for e in vp["events"]
                if e["lane"] == "forecast"
            ]
            shadow_events = [
                e for e in vp["events"]
                if e["lane"] == "shadow"
            ]

            assert len(forecast_events) >= 3
            assert len(shadow_events) >= 1


class TestViewPackInvarianceSummary:
    """Test ViewPack invariance summary for UI badge."""

    def test_viewpack_contains_invariance_summary(self):
        """Test that ViewPack contains invariance summary in aggregates."""

        def run_signal(ctx):
            return {"signal": "ok"}

        def run_compress(ctx):
            return {"compress": "ok"}

        def run_overlay(ctx):
            return {"overlay": "ok"}

        with tempfile.TemporaryDirectory() as tmpdir:
            result = abraxas_tick(
                tick=0,
                run_id="vp-inv",
                mode="test",
                context={},
                artifacts_dir=tmpdir,
                run_signal=run_signal,
                run_compress=run_compress,
                run_overlay=run_overlay,
            )

            vp_path = Path(result["artifacts"]["viewpack"])
            with open(vp_path) as f:
                vp = json.load(f)

            # Check invariance summary exists in aggregates
            assert "aggregates" in vp
            agg = vp["aggregates"]
            assert "invariance" in agg

            inv = agg["invariance"]
            assert inv["schema"] == "InvarianceSummary.v0"
            assert "trendpack_sha256" in inv
            assert "runheader_sha256" in inv
            assert "passed" in inv

            # Both hashes should be present and passed should be True
            assert isinstance(inv["trendpack_sha256"], str)
            assert len(inv["trendpack_sha256"]) == 64  # SHA-256 hex
            assert isinstance(inv["runheader_sha256"], str)
            assert len(inv["runheader_sha256"]) == 64
            assert inv["passed"] is True

    def test_viewpack_invariance_matches_artifact_hashes(self):
        """Test that invariance hashes match artifact return values."""

        def run_signal(ctx):
            return {"signal": "ok"}

        def run_compress(ctx):
            return {"compress": "ok"}

        def run_overlay(ctx):
            return {"overlay": "ok"}

        with tempfile.TemporaryDirectory() as tmpdir:
            result = abraxas_tick(
                tick=0,
                run_id="vp-inv-match",
                mode="test",
                context={},
                artifacts_dir=tmpdir,
                run_signal=run_signal,
                run_compress=run_compress,
                run_overlay=run_overlay,
            )

            vp_path = Path(result["artifacts"]["viewpack"])
            with open(vp_path) as f:
                vp = json.load(f)

            inv = vp["aggregates"]["invariance"]

            # Hashes should match what's returned by tick
            assert inv["trendpack_sha256"] == result["artifacts"]["trendpack_sha256"]
            assert inv["runheader_sha256"] == result["artifacts"]["run_header_sha256"]


class TestViewPackDeterminism:
    """Test that ViewPack is semantically deterministic."""

    def test_viewpack_content_is_deterministic(self):
        """Test that same inputs produce semantically identical ViewPack.

        Note: Raw sha256 may differ between runs due to embedded hashes
        (trendpack_sha256, runheader_sha256) which vary per artifacts_dir.
        But the semantic content (events, aggregates structure, stats) is deterministic.
        """

        def run_signal(ctx):
            return {"signal": "ok"}

        def run_compress(ctx):
            return {"compress": "ok"}

        def run_overlay(ctx):
            return {"overlay": "ok"}

        with tempfile.TemporaryDirectory() as tmpdir1, \
             tempfile.TemporaryDirectory() as tmpdir2:

            result1 = abraxas_tick(
                tick=0,
                run_id="vp-det",
                mode="test",
                context={},
                artifacts_dir=tmpdir1,
                run_signal=run_signal,
                run_compress=run_compress,
                run_overlay=run_overlay,
            )

            result2 = abraxas_tick(
                tick=0,
                run_id="vp-det",
                mode="test",
                context={},
                artifacts_dir=tmpdir2,
                run_signal=run_signal,
                run_compress=run_compress,
                run_overlay=run_overlay,
            )

            vp1_path = Path(result1["artifacts"]["viewpack"])
            vp2_path = Path(result2["artifacts"]["viewpack"])

            with open(vp1_path) as f:
                vp1 = json.load(f)
            with open(vp2_path) as f:
                vp2 = json.load(f)

            # Schema, run_id, tick, mode should match exactly
            assert vp1["schema"] == vp2["schema"]
            assert vp1["run_id"] == vp2["run_id"]
            assert vp1["tick"] == vp2["tick"]
            assert vp1["mode"] == vp2["mode"]

            # Events should be identical (excluding any path-dependent meta)
            assert len(vp1["events"]) == len(vp2["events"])
            for e1, e2 in zip(vp1["events"], vp2["events"]):
                assert e1["task"] == e2["task"]
                assert e1["lane"] == e2["lane"]
                assert e1["status"] == e2["status"]
                assert e1["cost_ops"] == e2["cost_ops"]

            # Aggregates stats/budget should match
            assert vp1["aggregates"]["stats"] == vp2["aggregates"]["stats"]
            assert vp1["aggregates"]["budget"] == vp2["aggregates"]["budget"]
            assert vp1["aggregates"]["error_count"] == vp2["aggregates"]["error_count"]
            assert vp1["aggregates"]["skipped_count"] == vp2["aggregates"]["skipped_count"]

            # Invariance summary schema and passed flag should match
            inv1 = vp1["aggregates"]["invariance"]
            inv2 = vp2["aggregates"]["invariance"]
            assert inv1["schema"] == inv2["schema"]
            assert inv1["passed"] == inv2["passed"]
            # Note: trendpack_sha256/runheader_sha256 may differ per dir (expected)
