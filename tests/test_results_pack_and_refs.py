"""
Tests for ResultsPack and result refs system.

Verifies:
- ResultsPack artifact is written
- TrendPack events contain result_ref
- RunIndex references both TrendPack and ResultsPack
- Result refs point to correct ResultsPack location
"""

import json
import tempfile
from pathlib import Path

import pytest

from abraxas.runtime import abraxas_tick
from abraxas.runtime.results_pack import build_results_pack, make_result_ref
from abraxas.ers.types import TaskResult


class TestBuildResultsPack:
    """Test build_results_pack() function."""

    def test_builds_results_pack(self):
        """Test that build_results_pack creates valid structure."""
        results = {
            "task_b": TaskResult(name="task_b", lane="forecast", status="ok", value={"b": 2}),
            "task_a": TaskResult(name="task_a", lane="forecast", status="ok", value={"a": 1}),
        }

        pack = build_results_pack(
            run_id="test-run",
            tick=0,
            results=results,
            provenance={"engine": "test"},
        )

        assert pack["schema"] == "ResultsPack.v0"
        assert pack["run_id"] == "test-run"
        assert pack["tick"] == 0
        assert "items" in pack
        assert "provenance" in pack

    def test_items_sorted_by_task_name(self):
        """Test that items are sorted by task name for determinism."""
        results = {
            "zebra": TaskResult(name="zebra", lane="shadow", status="ok"),
            "alpha": TaskResult(name="alpha", lane="forecast", status="ok"),
            "middle": TaskResult(name="middle", lane="shadow", status="ok"),
        }

        pack = build_results_pack(
            run_id="test", tick=0, results=results, provenance={}
        )

        task_names = [item["task"] for item in pack["items"]]
        assert task_names == ["alpha", "middle", "zebra"]

    def test_provenance_keys_sorted(self):
        """Test that provenance keys are sorted for determinism."""
        pack = build_results_pack(
            run_id="test",
            tick=0,
            results={},
            provenance={"z_key": 1, "a_key": 2, "m_key": 3},
        )

        prov_keys = list(pack["provenance"].keys())
        assert prov_keys == sorted(prov_keys)


class TestMakeResultRef:
    """Test make_result_ref() function."""

    def test_creates_result_ref(self):
        """Test that make_result_ref creates valid structure."""
        ref = make_result_ref(
            results_pack_path="/path/to/results.json",
            task_name="shadow:anagram",
        )

        assert ref["schema"] == "ResultRef.v0"
        assert ref["results_pack"] == "/path/to/results.json"
        assert ref["task"] == "shadow:anagram"


class TestTickEmitsResultsPack:
    """Test that abraxas_tick() emits ResultsPack and result_refs."""

    def test_tick_emits_results_pack(self):
        """Test that tick emits ResultsPack artifact."""

        def run_signal(ctx):
            return {"signal": "ok"}

        def run_compress(ctx):
            return {"compress": "ok"}

        def run_overlay(ctx):
            return {"overlay": "ok"}

        with tempfile.TemporaryDirectory() as tmpdir:
            result = abraxas_tick(
                tick=0,
                run_id="test-rp",
                mode="test",
                context={},
                artifacts_dir=tmpdir,
                run_signal=run_signal,
                run_compress=run_compress,
                run_overlay=run_overlay,
            )

            # Verify ResultsPack path in artifacts
            assert "results_pack" in result["artifacts"]
            assert "results_pack_sha256" in result["artifacts"]

            # Verify file exists
            rp_path = Path(result["artifacts"]["results_pack"])
            assert rp_path.exists()

            # Verify structure
            with open(rp_path) as f:
                rp = json.load(f)

            assert rp["schema"] == "ResultsPack.v0"
            assert rp["run_id"] == "test-rp"
            assert rp["tick"] == 0
            assert len(rp["items"]) >= 3  # At least 3 oracle tasks

    def test_trendpack_events_have_result_ref(self):
        """Test that TrendPack events contain result_ref in meta."""

        def run_signal(ctx):
            return {"signal": "ok"}

        def run_compress(ctx):
            return {"compress": "ok"}

        def run_overlay(ctx):
            return {"overlay": "ok"}

        with tempfile.TemporaryDirectory() as tmpdir:
            result = abraxas_tick(
                tick=0,
                run_id="test-refs",
                mode="test",
                context={},
                artifacts_dir=tmpdir,
                run_signal=run_signal,
                run_compress=run_compress,
                run_overlay=run_overlay,
            )

            # Load TrendPack
            tp_path = Path(result["artifacts"]["trendpack"])
            with open(tp_path) as f:
                tp = json.load(f)

            # Check that at least one event has result_ref
            events_with_ref = [
                e for e in tp["timeline"]
                if "result_ref" in (e.get("meta") or {})
            ]
            assert len(events_with_ref) > 0

            # Verify result_ref structure
            first_ref = events_with_ref[0]["meta"]["result_ref"]
            assert first_ref["schema"] == "ResultRef.v0"
            assert "results_pack" in first_ref
            assert "task" in first_ref

    def test_runindex_references_both_artifacts(self):
        """Test that RunIndex references both TrendPack and ResultsPack."""

        def run_signal(ctx):
            return {"signal": "ok"}

        def run_compress(ctx):
            return {"compress": "ok"}

        def run_overlay(ctx):
            return {"overlay": "ok"}

        with tempfile.TemporaryDirectory() as tmpdir:
            result = abraxas_tick(
                tick=0,
                run_id="test-runindex",
                mode="test",
                context={},
                artifacts_dir=tmpdir,
                run_signal=run_signal,
                run_compress=run_compress,
                run_overlay=run_overlay,
            )

            # Load RunIndex
            ri_path = Path(result["artifacts"]["runindex"])
            with open(ri_path) as f:
                ri = json.load(f)

            # Verify both refs exist
            assert "trendpack" in ri["refs"]
            assert "results_pack" in ri["refs"]

            # Verify both hashes exist
            assert "trendpack_sha256" in ri["hashes"]
            assert "results_pack_sha256" in ri["hashes"]

    def test_result_ref_points_to_correct_task(self):
        """Test that result_ref task matches the event task."""

        def run_signal(ctx):
            return {"signal": "ok"}

        def run_compress(ctx):
            return {"compress": "ok"}

        def run_overlay(ctx):
            return {"overlay": "ok"}

        with tempfile.TemporaryDirectory() as tmpdir:
            result = abraxas_tick(
                tick=0,
                run_id="test-match",
                mode="test",
                context={},
                artifacts_dir=tmpdir,
                run_signal=run_signal,
                run_compress=run_compress,
                run_overlay=run_overlay,
            )

            # Load TrendPack
            tp_path = Path(result["artifacts"]["trendpack"])
            with open(tp_path) as f:
                tp = json.load(f)

            # Verify each event's result_ref.task matches event.task
            for event in tp["timeline"]:
                result_ref = event.get("meta", {}).get("result_ref")
                if result_ref:
                    assert result_ref["task"] == event["task"]


class TestResultsPackWithShadowTasks:
    """Test ResultsPack with shadow tasks (normalized outputs)."""

    def test_shadow_tasks_in_results_pack(self):
        """Test that shadow task results are in ResultsPack."""

        def run_signal(ctx):
            return {"signal": "ok"}

        def run_compress(ctx):
            return {"compress": "ok"}

        def run_overlay(ctx):
            return {"overlay": "ok"}

        def shadow_test(ctx):
            return {"status": "ok", "value": {"test": 42}}

        with tempfile.TemporaryDirectory() as tmpdir:
            result = abraxas_tick(
                tick=0,
                run_id="test-shadow-rp",
                mode="test",
                context={},
                artifacts_dir=tmpdir,
                run_signal=run_signal,
                run_compress=run_compress,
                run_overlay=run_overlay,
                run_shadow_tasks={"test": shadow_test},
            )

            # Load ResultsPack
            rp_path = Path(result["artifacts"]["results_pack"])
            with open(rp_path) as f:
                rp = json.load(f)

            # Find shadow task in items
            shadow_items = [
                item for item in rp["items"]
                if item["task"].startswith("shadow:")
            ]
            assert len(shadow_items) > 0

            # Verify shadow task result structure
            shadow_item = shadow_items[0]
            assert "result" in shadow_item
            assert shadow_item["result"]["lane"] == "shadow"


class TestDeterminism:
    """Test that ResultsPack and refs are deterministic."""

    def test_results_pack_is_deterministic(self):
        """Test that same inputs produce same ResultsPack."""

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
                run_id="test-det",
                mode="test",
                context={},
                artifacts_dir=tmpdir1,
                run_signal=run_signal,
                run_compress=run_compress,
                run_overlay=run_overlay,
            )

            result2 = abraxas_tick(
                tick=0,
                run_id="test-det",
                mode="test",
                context={},
                artifacts_dir=tmpdir2,
                run_signal=run_signal,
                run_compress=run_compress,
                run_overlay=run_overlay,
            )

            # ResultsPack SHA-256 should match (same content)
            assert result1["artifacts"]["results_pack_sha256"] == \
                   result2["artifacts"]["results_pack_sha256"]
