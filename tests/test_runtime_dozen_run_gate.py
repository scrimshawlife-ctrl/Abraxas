from tempfile import TemporaryDirectory

from abraxas.runtime.invariance_gate import dozen_run_tick_invariance_gate
from abraxas.runtime.tick import abraxas_tick


def test_runtime_dozen_run_gate_passes_for_deterministic_tick():
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
        assert all(h == res.expected_sha256 for h in res.sha256s)


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
        assert "event_index" in res.divergence
        assert "diff" in res.divergence
