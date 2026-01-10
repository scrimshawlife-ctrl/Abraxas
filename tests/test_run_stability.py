"""
Tests for RunStability.v0 artifact.

Verifies:
- RunStability is written correctly from gate result
- StabilityRef is written and references RunStability
- RunHeader includes stability_ref_path convention
- Load and verify functions work correctly
"""

import json
import tempfile
from pathlib import Path

import pytest

from abraxas.runtime import (
    abraxas_tick,
    ensure_run_header,
    load_run_header,
)
from abraxas.runtime.run_stability import (
    write_run_stability,
    write_stability_ref,
    load_run_stability,
    load_stability_ref,
    verify_run_stability,
    get_stability_ref_path,
)
from abraxas.runtime.invariance_gate import dozen_run_tick_invariance_gate


class TestWriteRunStability:
    """Test write_run_stability() function."""

    def test_writes_run_stability_pass(self):
        """Test writing RunStability.v0 for pass result."""
        with tempfile.TemporaryDirectory() as tmpdir:
            gate_result = {
                "ok": True,
                "expected_sha256": "abc123",
                "sha256s": ["abc123"] * 12,
                "expected_runheader_sha256": "def456",
                "runheader_sha256s": ["def456"] * 12,
                "first_mismatch_run": None,
                "divergence": None,
            }

            path, sha256 = write_run_stability(
                artifacts_dir=tmpdir,
                run_id="test_run",
                gate_result=gate_result,
                note="test pass",
            )

            # Verify file exists
            assert Path(path).exists()
            assert path.endswith("test_run.runstability.json")

            # Verify content
            with open(path) as f:
                stability = json.load(f)

            assert stability["schema"] == "RunStability.v0"
            assert stability["run_id"] == "test_run"
            assert stability["ok"] is True
            assert stability["expected_trendpack_sha256"] == "abc123"
            assert stability["expected_runheader_sha256"] == "def456"
            assert stability["note"] == "test pass"

    def test_writes_run_stability_fail(self):
        """Test writing RunStability.v0 for fail result."""
        with tempfile.TemporaryDirectory() as tmpdir:
            gate_result = {
                "ok": False,
                "expected_sha256": "abc123",
                "sha256s": ["abc123", "xyz789"],
                "expected_runheader_sha256": "def456",
                "runheader_sha256s": ["def456", "def456"],
                "first_mismatch_run": 1,
                "divergence": {"kind": "trendpack_content_mismatch", "diff": {}},
            }

            path, sha256 = write_run_stability(
                artifacts_dir=tmpdir,
                run_id="fail_run",
                gate_result=gate_result,
                note="test failure",
            )

            # Verify content
            stability = load_run_stability(path)
            assert stability["ok"] is False
            assert stability["first_mismatch_run"] == 1
            assert stability["divergence"]["kind"] == "trendpack_content_mismatch"

    def test_stability_path_structure(self):
        """Test that stability is written to correct path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path, _ = write_run_stability(
                artifacts_dir=tmpdir,
                run_id="my_run",
                gate_result={"ok": True},
            )

            expected = Path(tmpdir) / "runs" / "my_run.runstability.json"
            assert Path(path) == expected


class TestWriteStabilityRef:
    """Test write_stability_ref() function."""

    def test_writes_stability_ref(self):
        """Test writing StabilityRef.v0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # First write stability
            stability_path, stability_sha = write_run_stability(
                artifacts_dir=tmpdir,
                run_id="ref_test",
                gate_result={"ok": True},
            )

            # Then write ref
            ref_path, ref_sha = write_stability_ref(
                artifacts_dir=tmpdir,
                run_id="ref_test",
                runstability_path=stability_path,
                runstability_sha256=stability_sha,
            )

            # Verify ref file exists
            assert Path(ref_path).exists()
            assert ref_path.endswith("ref_test.stability_ref.json")

            # Verify ref content
            ref = load_stability_ref(ref_path)
            assert ref["schema"] == "StabilityRef.v0"
            assert ref["run_id"] == "ref_test"
            assert ref["runstability_path"] == stability_path
            assert ref["runstability_sha256"] == stability_sha


class TestLoadRunStability:
    """Test load_run_stability() function."""

    def test_loads_existing_stability(self):
        """Test loading existing RunStability.v0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path, _ = write_run_stability(
                artifacts_dir=tmpdir,
                run_id="load_test",
                gate_result={"ok": True, "expected_sha256": "test123"},
            )

            stability = load_run_stability(path)
            assert stability["schema"] == "RunStability.v0"
            assert stability["ok"] is True

    def test_raises_for_missing_stability(self):
        """Test that missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_run_stability("/nonexistent/path.json")

    def test_raises_for_invalid_schema(self):
        """Test that invalid schema raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_file = Path(tmpdir) / "bad.json"
            bad_file.write_text('{"schema": "Wrong.v0"}')

            with pytest.raises(ValueError, match="Invalid run stability schema"):
                load_run_stability(str(bad_file))


class TestVerifyRunStability:
    """Test verify_run_stability() function."""

    def test_verifies_valid_stability(self):
        """Test verification of valid stability file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path, sha256 = write_run_stability(
                artifacts_dir=tmpdir,
                run_id="verify_test",
                gate_result={"ok": True},
            )

            result = verify_run_stability(path, sha256)
            assert result["valid"] is True
            assert result["actual_sha256"] == sha256

    def test_detects_missing_stability(self):
        """Test detection of missing stability file."""
        result = verify_run_stability("/nonexistent/path.json", "abc123")
        assert result["valid"] is False
        assert "missing" in result["reason"].lower()

    def test_detects_hash_mismatch(self):
        """Test detection of hash mismatch."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path, _ = write_run_stability(
                artifacts_dir=tmpdir,
                run_id="mismatch_test",
                gate_result={"ok": True},
            )

            result = verify_run_stability(path, "wrong_hash")
            assert result["valid"] is False
            assert "mismatch" in result["reason"].lower()


class TestRunHeaderStabilityRef:
    """Test that RunHeader includes stability_ref_pattern convention."""

    def test_run_header_contains_stability_ref_pattern(self):
        """Test that RunHeader.v0 includes stability_ref_pattern."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path, _ = ensure_run_header(
                artifacts_dir=tmpdir,
                run_id="header_test",
                mode="test",
                pipeline_bindings_provenance={"test": True},
                policy_refs={},
            )

            header = load_run_header(path)
            assert "stability_ref_pattern" in header
            assert header["stability_ref_pattern"] == "runs/header_test.stability_ref.json"

    def test_stability_ref_pattern_is_relative(self):
        """Test that stability_ref_pattern is relative (not absolute)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path, _ = ensure_run_header(
                artifacts_dir=tmpdir,
                run_id="relative_test",
                mode="test",
                pipeline_bindings_provenance={},
                policy_refs={},
            )

            header = load_run_header(path)
            # Should be relative (no leading /)
            assert not header["stability_ref_pattern"].startswith("/")
            assert header["stability_ref_pattern"] == "runs/relative_test.stability_ref.json"


class TestIntegrationWithGate:
    """Test integration with dozen-run invariance gate."""

    def test_full_stability_workflow(self):
        """Test full workflow: gate -> stability -> ref."""
        with tempfile.TemporaryDirectory() as tmpdir:
            def run_signal(ctx): return {"signal": 1}
            def run_compress(ctx): return {"compress": 1}
            def run_overlay(ctx): return {"overlay": 1}

            def run_once(i: int, artifacts_dir: str):
                return abraxas_tick(
                    tick=0,
                    run_id="workflow_test",
                    mode="sandbox",
                    context={},
                    artifacts_dir=artifacts_dir,
                    run_signal=run_signal,
                    run_compress=run_compress,
                    run_overlay=run_overlay,
                )

            # Run gate
            res = dozen_run_tick_invariance_gate(
                base_artifacts_dir=tmpdir,
                runs=3,
                run_once=run_once,
            )

            # Build gate result dict
            gate_obj = {
                "ok": res.ok,
                "expected_sha256": res.expected_sha256,
                "sha256s": res.sha256s,
                "expected_runheader_sha256": res.expected_runheader_sha256,
                "runheader_sha256s": res.runheader_sha256s,
                "first_mismatch_run": res.first_mismatch_run,
                "divergence": res.divergence,
            }

            # Write stability
            stability_path, stability_sha = write_run_stability(
                artifacts_dir=tmpdir,
                run_id="workflow_test",
                gate_result=gate_obj,
                note="integration test",
            )

            # Write ref
            ref_path, ref_sha = write_stability_ref(
                artifacts_dir=tmpdir,
                run_id="workflow_test",
                runstability_path=stability_path,
                runstability_sha256=stability_sha,
            )

            # Verify chain
            stability = load_run_stability(stability_path)
            ref = load_stability_ref(ref_path)

            assert stability["ok"] == res.ok
            assert ref["runstability_sha256"] == stability_sha

            # Verify hash chain integrity
            verify_result = verify_run_stability(
                ref["runstability_path"],
                ref["runstability_sha256"],
            )
            assert verify_result["valid"] is True


class TestStabilityDeterminism:
    """Test that RunStability is deterministic."""

    def test_same_gate_result_produces_same_hash(self):
        """Test that same gate result produces same stability hash."""
        with tempfile.TemporaryDirectory() as tmpdir1, \
             tempfile.TemporaryDirectory() as tmpdir2:

            gate_result = {
                "ok": True,
                "expected_sha256": "abc123",
                "sha256s": ["abc123", "abc123", "abc123"],
                "expected_runheader_sha256": "def456",
                "runheader_sha256s": ["def456", "def456", "def456"],
                "first_mismatch_run": None,
                "divergence": None,
            }

            _, sha1 = write_run_stability(
                artifacts_dir=tmpdir1,
                run_id="det_test",
                gate_result=gate_result,
                note="test",
            )

            _, sha2 = write_run_stability(
                artifacts_dir=tmpdir2,
                run_id="det_test",
                gate_result=gate_result,
                note="test",
            )

            assert sha1 == sha2
