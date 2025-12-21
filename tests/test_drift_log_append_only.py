"""Test drift log append-only behavior."""
from __future__ import annotations
import json
import tempfile
from pathlib import Path
import pytest
from abx.core.pipeline import run_oracle


def test_drift_log_appends_on_each_run():
    """Test that drift log appends one line per oracle run."""
    # Use temporary log file for isolation
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "test_drift.log.jsonl"

        # Monkey-patch the default log path for testing
        import abx.oracle.drift as drift_module
        original_append = drift_module.append_drift_log

        def patched_append(*args, **kwargs):
            kwargs["log_path"] = log_path
            return original_append(*args, **kwargs)

        drift_module.append_drift_log = patched_append

        try:
            # Run oracle twice
            input_obj = {"intent": "log_test", "v": 1}
            run_oracle(input_obj, anchor="test_anchor_1")
            run_oracle(input_obj, anchor="test_anchor_2")

            # Assert log file exists
            assert log_path.exists(), "Log file must be created"

            # Read log lines
            with open(log_path) as f:
                lines = f.readlines()

            # Assert exactly 2 lines appended
            assert len(lines) == 2, f"Expected 2 log lines, got {len(lines)}"

            # Parse each line as JSON
            for i, line in enumerate(lines):
                entry = json.loads(line)
                assert "utc" in entry
                assert "anchor" in entry
                assert "drift_magnitude" in entry
                assert "integrity_score" in entry
                assert "auto_recenter" in entry
                assert "gate_state" in entry
                assert "runes_used" in entry
                assert "manifest_sha256" in entry

            # Assert different anchors were logged
            entry_1 = json.loads(lines[0])
            entry_2 = json.loads(lines[1])
            assert entry_1["anchor"] == "test_anchor_1"
            assert entry_2["anchor"] == "test_anchor_2"

        finally:
            # Restore original function
            drift_module.append_drift_log = original_append


def test_drift_log_never_overwrites():
    """Test that drift log is strictly append-only."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "test_drift_append.log.jsonl"

        # Monkey-patch
        import abx.oracle.drift as drift_module
        original_append = drift_module.append_drift_log

        def patched_append(*args, **kwargs):
            kwargs["log_path"] = log_path
            return original_append(*args, **kwargs)

        drift_module.append_drift_log = patched_append

        try:
            input_obj = {"intent": "append_test", "v": 1}

            # Run 5 times
            for i in range(5):
                run_oracle(input_obj, anchor=f"anchor_{i}")

            # Assert 5 lines
            with open(log_path) as f:
                lines = f.readlines()
            assert len(lines) == 5

            # Run 3 more times
            for i in range(5, 8):
                run_oracle(input_obj, anchor=f"anchor_{i}")

            # Assert now 8 lines (appended, not overwritten)
            with open(log_path) as f:
                lines = f.readlines()
            assert len(lines) == 8

            # Verify all anchors are present
            anchors = [json.loads(line)["anchor"] for line in lines]
            assert anchors == [f"anchor_{i}" for i in range(8)]

        finally:
            drift_module.append_drift_log = original_append


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
