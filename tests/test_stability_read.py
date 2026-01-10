"""
Tests for stability_read utility module.

Verifies:
- read_run_stability returns None when absent
- read_run_stability reads via StabilityRef
- read_run_stability reads direct RunStability
- read_stability_summary returns compact format
- stability_exists check works
"""

import json
import tempfile
from pathlib import Path

import pytest

from abraxas.runtime.stability_read import (
    read_run_stability,
    read_stability_summary,
    stability_exists,
)
from abraxas.runtime.run_stability import (
    write_run_stability,
    write_stability_ref,
)


class TestReadRunStability:
    """Test read_run_stability() function."""

    def test_returns_none_when_absent(self):
        """Test that missing stability returns None."""
        with tempfile.TemporaryDirectory() as d:
            assert read_run_stability(d, "nope") is None

    def test_reads_direct_stability(self):
        """Test reading direct RunStability.v0 file."""
        with tempfile.TemporaryDirectory() as d:
            runs_dir = Path(d) / "runs"
            runs_dir.mkdir(parents=True, exist_ok=True)

            stability_file = runs_dir / "direct_run.runstability.json"
            stability_file.write_text(
                json.dumps({
                    "schema": "RunStability.v0",
                    "run_id": "direct_run",
                    "ok": True,
                    "expected_trendpack_sha256": "abc123",
                }),
                encoding="utf-8",
            )

            result = read_run_stability(d, "direct_run")
            assert result is not None
            assert result["schema"] == "RunStability.v0"
            assert result["run_id"] == "direct_run"
            assert result["ok"] is True

    def test_reads_via_stability_ref(self):
        """Test reading stability via StabilityRef.v0."""
        with tempfile.TemporaryDirectory() as d:
            # Write stability and ref using official functions
            stability_path, stability_sha = write_run_stability(
                artifacts_dir=d,
                run_id="ref_run",
                gate_result={"ok": False, "expected_sha256": "xyz"},
                note="test via ref",
            )

            write_stability_ref(
                artifacts_dir=d,
                run_id="ref_run",
                runstability_path=stability_path,
                runstability_sha256=stability_sha,
            )

            result = read_run_stability(d, "ref_run")
            assert result is not None
            assert result["schema"] == "RunStability.v0"
            assert result["ok"] is False
            assert result["note"] == "test via ref"

    def test_prefers_ref_over_direct(self):
        """Test that StabilityRef is preferred over direct file."""
        with tempfile.TemporaryDirectory() as d:
            # Write stability via ref
            stability_path, stability_sha = write_run_stability(
                artifacts_dir=d,
                run_id="pref_run",
                gate_result={"ok": True},
                note="via ref",
            )

            write_stability_ref(
                artifacts_dir=d,
                run_id="pref_run",
                runstability_path=stability_path,
                runstability_sha256=stability_sha,
            )

            result = read_run_stability(d, "pref_run")
            assert result is not None
            assert result["note"] == "via ref"

    def test_handles_malformed_ref_gracefully(self):
        """Test that malformed StabilityRef returns None."""
        with tempfile.TemporaryDirectory() as d:
            runs_dir = Path(d) / "runs"
            runs_dir.mkdir(parents=True, exist_ok=True)

            # Write malformed ref
            ref_file = runs_dir / "bad_run.stability_ref.json"
            ref_file.write_text('{"schema": "StabilityRef.v0", "runstability_path": "/nonexistent"}')

            result = read_run_stability(d, "bad_run")
            assert result is None

    def test_handles_invalid_json_gracefully(self):
        """Test that invalid JSON returns None."""
        with tempfile.TemporaryDirectory() as d:
            runs_dir = Path(d) / "runs"
            runs_dir.mkdir(parents=True, exist_ok=True)

            # Write invalid JSON
            stability_file = runs_dir / "invalid.runstability.json"
            stability_file.write_text("not valid json {{{")

            result = read_run_stability(d, "invalid")
            assert result is None


class TestReadStabilitySummary:
    """Test read_stability_summary() function."""

    def test_returns_none_when_absent(self):
        """Test that missing stability returns None."""
        with tempfile.TemporaryDirectory() as d:
            assert read_stability_summary(d, "missing") is None

    def test_returns_summary_for_pass(self):
        """Test summary for passing stability."""
        with tempfile.TemporaryDirectory() as d:
            write_run_stability(
                artifacts_dir=d,
                run_id="pass_run",
                gate_result={
                    "ok": True,
                    "first_mismatch_run": None,
                    "divergence": None,
                },
            )

            summary = read_stability_summary(d, "pass_run")
            assert summary is not None
            assert summary["schema"] == "StabilitySummary.v0"
            assert summary["ok"] is True
            assert summary["first_mismatch_run"] is None
            assert summary["divergence_kind"] is None

    def test_returns_summary_for_fail(self):
        """Test summary for failing stability."""
        with tempfile.TemporaryDirectory() as d:
            write_run_stability(
                artifacts_dir=d,
                run_id="fail_run",
                gate_result={
                    "ok": False,
                    "first_mismatch_run": 3,
                    "divergence": {
                        "kind": "trendpack_content_mismatch",
                        "event_index": 0,
                        "diff": {"a": 1, "b": 2},
                    },
                },
            )

            summary = read_stability_summary(d, "fail_run")
            assert summary is not None
            assert summary["schema"] == "StabilitySummary.v0"
            assert summary["ok"] is False
            assert summary["first_mismatch_run"] == 3
            assert summary["divergence_kind"] == "trendpack_content_mismatch"


class TestStabilityExists:
    """Test stability_exists() function."""

    def test_returns_false_when_absent(self):
        """Test that missing stability returns False."""
        with tempfile.TemporaryDirectory() as d:
            assert stability_exists(d, "nope") is False

    def test_returns_true_when_present(self):
        """Test that existing stability returns True."""
        with tempfile.TemporaryDirectory() as d:
            write_run_stability(
                artifacts_dir=d,
                run_id="exists_run",
                gate_result={"ok": True},
            )

            assert stability_exists(d, "exists_run") is True

    def test_returns_false_for_invalid(self):
        """Test that invalid stability returns False."""
        with tempfile.TemporaryDirectory() as d:
            runs_dir = Path(d) / "runs"
            runs_dir.mkdir(parents=True, exist_ok=True)

            # Write file with wrong schema
            stability_file = runs_dir / "wrong.runstability.json"
            stability_file.write_text('{"schema": "Wrong.v0"}')

            assert stability_exists(d, "wrong") is False
