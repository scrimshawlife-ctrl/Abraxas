"""
Tests for abraxas.runtime.tick orchestrator.
"""

import tempfile
from pathlib import Path
import json

from abraxas.runtime import abraxas_tick


def test_abraxas_tick_basic_execution():
    """Test basic tick execution with artifact emission."""
    call_order = []

    def run_signal(ctx):
        call_order.append("signal")
        return {"signal": "ok"}

    def run_compress(ctx):
        call_order.append("compress")
        return {"compress": "ok"}

    def run_overlay(ctx):
        call_order.append("overlay")
        return {"overlay": "ok"}

    with tempfile.TemporaryDirectory() as tmpdir:
        result = abraxas_tick(
            tick=0,
            run_id="TEST-RUN-001",
            mode="test",
            context={},
            artifacts_dir=tmpdir,
            run_signal=run_signal,
            run_compress=run_compress,
            run_overlay=run_overlay,
        )

        # Verify execution order (forecast lane, priority sorted)
        assert call_order == ["signal", "compress", "overlay"]

        # Verify result structure
        assert result["tick"] == 0
        assert result["run_id"] == "TEST-RUN-001"
        assert result["mode"] == "test"
        assert "results" in result
        assert "remaining" in result
        assert "artifacts" in result

        # Verify artifact was written
        artifact_path = result["artifacts"]["trendpack"]
        assert Path(artifact_path).exists()

        # Verify TrendPack structure
        with open(artifact_path) as f:
            trendpack = json.load(f)
        assert trendpack["version"] == "0.1"
        assert trendpack["run_id"] == "TEST-RUN-001"
        assert trendpack["tick"] == 0
        assert trendpack["provenance"]["engine"] == "abraxas"
        assert trendpack["provenance"]["mode"] == "test"
        assert trendpack["provenance"]["ers"] == "v0.2"


def test_abraxas_tick_with_shadow_tasks():
    """Test tick execution with shadow lane tasks."""
    call_order = []

    def run_signal(ctx):
        call_order.append("signal")
        return {"ok": True}

    def run_compress(ctx):
        call_order.append("compress")
        return {"ok": True}

    def run_overlay(ctx):
        call_order.append("overlay")
        return {"ok": True}

    def shadow_anagram(ctx):
        call_order.append("shadow:anagram")
        return {"ok": True}

    def shadow_sei(ctx):
        call_order.append("shadow:sei")
        return {"ok": True}

    with tempfile.TemporaryDirectory() as tmpdir:
        result = abraxas_tick(
            tick=0,
            run_id="TEST-RUN-002",
            mode="test",
            context={},
            artifacts_dir=tmpdir,
            run_signal=run_signal,
            run_compress=run_compress,
            run_overlay=run_overlay,
            run_shadow_tasks={
                "anagram": shadow_anagram,
                "sei": shadow_sei,
            },
        )

        # Forecast tasks run before shadow tasks
        assert call_order[:3] == ["signal", "compress", "overlay"]
        # Shadow tasks run in sorted order
        assert set(call_order[3:]) == {"shadow:anagram", "shadow:sei"}

        # Verify TrendPack includes shadow events
        artifact_path = result["artifacts"]["trendpack"]
        with open(artifact_path) as f:
            trendpack = json.load(f)

        assert trendpack["stats"]["forecast_events"] == 3
        assert trendpack["stats"]["shadow_events"] == 2
        assert trendpack["stats"]["total_events"] == 5


def test_abraxas_tick_artifact_path_structure():
    """Test artifact path structure: artifacts_dir/viz/run_id/tick.trendpack.json"""
    def noop(ctx): return {}

    with tempfile.TemporaryDirectory() as tmpdir:
        result = abraxas_tick(
            tick=42,
            run_id="TEST-RUN-003",
            mode="test",
            context={},
            artifacts_dir=tmpdir,
            run_signal=noop,
            run_compress=noop,
            run_overlay=noop,
        )

        artifact_path = Path(result["artifacts"]["trendpack"])

        # Verify path structure
        assert artifact_path.parent.name == "TEST-RUN-003"
        assert artifact_path.parent.parent.name == "viz"
        assert artifact_path.name == "000042.trendpack.json"


def test_abraxas_tick_deterministic_artifact():
    """Test that identical ticks produce identical TrendPack artifacts."""
    def signal(ctx): return {"value": 1}
    def compress(ctx): return {"value": 2}
    def overlay(ctx): return {"value": 3}

    with tempfile.TemporaryDirectory() as tmpdir1, tempfile.TemporaryDirectory() as tmpdir2:
        result1 = abraxas_tick(
            tick=0,
            run_id="TEST-RUN-004",
            mode="test",
            context={},
            artifacts_dir=tmpdir1,
            run_signal=signal,
            run_compress=compress,
            run_overlay=overlay,
        )

        result2 = abraxas_tick(
            tick=0,
            run_id="TEST-RUN-004",
            mode="test",
            context={},
            artifacts_dir=tmpdir2,
            run_signal=signal,
            run_compress=compress,
            run_overlay=overlay,
        )

        # Load both TrendPacks
        with open(result1["artifacts"]["trendpack"]) as f1, open(result2["artifacts"]["trendpack"]) as f2:
            tp1 = json.load(f1)
            tp2 = json.load(f2)

        # Should be identical (deterministic)
        assert tp1 == tp2
