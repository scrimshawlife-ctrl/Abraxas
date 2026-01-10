"""
Tests for Abraxas Runtime Dozen-Run Invariance Gate.

Verifies:
- Gate passes for deterministic tick execution
- Gate detects TrendPack content drift
- Gate detects RunHeader drift
- RunHeader sha256s are tracked and verified
"""

from tempfile import TemporaryDirectory

from abraxas.runtime.invariance_gate import dozen_run_tick_invariance_gate
from abraxas.runtime.tick import abraxas_tick


def test_runtime_dozen_run_gate_passes_for_deterministic_tick():
    """Test that gate passes when all runs produce identical normalized artifacts."""
    with TemporaryDirectory() as d:
        def run_signal(ctx): return {"signal": 1}
        def run_compress(ctx): return {"compress": 1}
        def run_overlay(ctx): return {"overlay": 1}

        def run_once(i: int, artifacts_dir: str):
            # identical inputs, isolated artifacts dirs
            return abraxas_tick(
                tick=0,
                run_id="gate_test",
                mode="sandbox",
                context={"x": 1},
                artifacts_dir=artifacts_dir,
                run_signal=run_signal,
                run_compress=run_compress,
                run_overlay=run_overlay,
                run_shadow_tasks={"sei": lambda ctx: {"sei": 0}},
            )

        res = dozen_run_tick_invariance_gate(
            base_artifacts_dir=d,
            runs=12,
            run_once=run_once,
        )
        assert res.ok is True
        assert len(res.sha256s) == 12
        # Note: Raw sha256s differ due to path-dependent content (result_ref.results_pack)
        # The gate uses normalized comparison that strips paths

        # Verify RunHeader invariance is also tracked
        assert res.runheader_sha256s is not None
        assert len(res.runheader_sha256s) == 12
        assert res.expected_runheader_sha256 is not None
        # All RunHeader sha256s should be identical (content is path-independent)
        assert all(h == res.expected_runheader_sha256 for h in res.runheader_sha256s)


def test_runtime_dozen_run_gate_detects_drift():
    """Test that the gate catches non-deterministic artifact emission."""
    with TemporaryDirectory() as d:
        counter = {"value": 0}

        def run_signal(ctx):
            # Deliberately non-deterministic - fail on even runs
            counter["value"] += 1
            if counter["value"] % 2 == 0:
                raise ValueError("Drift induced")
            return {"signal": 1}

        def run_compress(ctx): return {"compress": 1}
        def run_overlay(ctx): return {"overlay": 1}

        def run_once_with_drift(i: int, artifacts_dir: str):
            # Deliberately non-deterministic trace
            return abraxas_tick(
                tick=0,
                run_id="gate_test_drift",
                mode="sandbox",
                context={"x": 1},
                artifacts_dir=artifacts_dir,
                run_signal=run_signal,
                run_compress=run_compress,
                run_overlay=run_overlay,
            )

        res = dozen_run_tick_invariance_gate(
            base_artifacts_dir=d,
            runs=12,
            run_once=run_once_with_drift,
        )
        assert res.ok is False
        assert res.first_mismatch_run == 1  # Second run differs
        assert res.divergence is not None
        # Gate now reports content mismatch (normalized comparison)
        assert res.divergence.get("kind") == "trendpack_content_mismatch"
        assert "event_index" in res.divergence
        assert "diff" in res.divergence

        # RunHeader sha256s should still be tracked
        assert res.runheader_sha256s is not None


def test_runtime_dozen_run_gate_result_structure():
    """Test that result contains all expected fields."""
    with TemporaryDirectory() as d:
        def run_signal(ctx): return {"signal": 1}
        def run_compress(ctx): return {"compress": 1}
        def run_overlay(ctx): return {"overlay": 1}

        def run_once(i: int, artifacts_dir: str):
            return abraxas_tick(
                tick=0,
                run_id="gate_test",
                mode="sandbox",
                context={},
                artifacts_dir=artifacts_dir,
                run_signal=run_signal,
                run_compress=run_compress,
                run_overlay=run_overlay,
            )

        res = dozen_run_tick_invariance_gate(
            base_artifacts_dir=d,
            runs=3,  # Use 3 runs for faster test
            run_once=run_once,
        )

        # Verify result structure
        assert res.ok is True
        assert res.expected_sha256 is not None
        assert res.sha256s is not None
        assert res.expected_runheader_sha256 is not None
        assert res.runheader_sha256s is not None
        assert res.first_mismatch_run is None
        assert res.divergence is None


def test_runtime_dozen_run_gate_runheader_identical_across_runs():
    """Test that RunHeader is identical across all runs for same config."""
    with TemporaryDirectory() as d:
        def run_signal(ctx): return {"signal": 1}
        def run_compress(ctx): return {"compress": 1}
        def run_overlay(ctx): return {"overlay": 1}

        def run_once(i: int, artifacts_dir: str):
            return abraxas_tick(
                tick=0,
                run_id="runheader_test",
                mode="test",
                context={"key": "value"},
                artifacts_dir=artifacts_dir,
                run_signal=run_signal,
                run_compress=run_compress,
                run_overlay=run_overlay,
            )

        res = dozen_run_tick_invariance_gate(
            base_artifacts_dir=d,
            runs=5,
            run_once=run_once,
        )

        assert res.ok is True

        # All RunHeader sha256s should be identical (path-independent)
        assert len(set(res.runheader_sha256s)) == 1

        # Note: Raw TrendPack sha256s differ due to path-dependent content
        # but gate passes because normalized content is identical
