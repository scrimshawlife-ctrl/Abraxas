"""
Tests for RunHeader.v0 run-level provenance system.

Verifies:
- RunHeader creation and structure
- RunHeader written once per run_id (reused on subsequent ticks)
- RunHeader contains expected provenance fields
- RunHeader verification
- RunHeader integration with tick artifacts
"""

import json
import tempfile
from pathlib import Path

import pytest

from abraxas.runtime import (
    abraxas_tick,
)
from abraxas.runtime.run_header import (
    ensure_run_header,
    load_run_header,
    verify_run_header,
)


class TestEnsureRunHeader:
    """Test ensure_run_header() function."""

    def test_creates_run_header(self):
        """Test run header creation with expected structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path, sha256 = ensure_run_header(
                artifacts_dir=tmpdir,
                run_id="test-run",
                mode="test",
                pipeline_bindings_provenance={"bindings": "test"},
                policy_refs={"retention": {"schema": "PolicyRef.v0", "policy": "retention"}},
            )

            # Verify file was created
            assert Path(path).exists()
            assert len(sha256) == 64  # SHA-256 hex length

            # Verify structure
            with open(path) as f:
                header = json.load(f)

            assert header["schema"] == "RunHeader.v0"
            assert header["run_id"] == "test-run"
            assert header["mode"] == "test"
            assert "code" in header
            assert "pipeline_bindings" in header
            assert "policy_refs" in header
            assert "env" in header

    def test_header_path_structure(self):
        """Test that header is written to runs/<run_id>.runheader.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path, _ = ensure_run_header(
                artifacts_dir=tmpdir,
                run_id="my-run-id",
                mode="test",
                pipeline_bindings_provenance={},
                policy_refs={},
            )

            assert "runs" in path
            assert "my-run-id.runheader.json" in path

    def test_header_reused_on_subsequent_calls(self):
        """Test that same run_id reuses existing header (not overwritten)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # First call
            path1, sha1 = ensure_run_header(
                artifacts_dir=tmpdir,
                run_id="test-run",
                mode="test",
                pipeline_bindings_provenance={"first": True},
                policy_refs={},
            )

            # Second call with different provenance (should be ignored)
            path2, sha2 = ensure_run_header(
                artifacts_dir=tmpdir,
                run_id="test-run",
                mode="test",
                pipeline_bindings_provenance={"second": True},
                policy_refs={},
            )

            # Should return same path and hash (not overwritten)
            assert path1 == path2
            assert sha1 == sha2

            # Verify content still has first call's provenance
            with open(path1) as f:
                header = json.load(f)
            assert header["pipeline_bindings"] == {"first": True}

    def test_header_contains_env_fingerprint(self):
        """Test that header contains environment fingerprint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path, _ = ensure_run_header(
                artifacts_dir=tmpdir,
                run_id="test-run",
                mode="test",
                pipeline_bindings_provenance={},
                policy_refs={},
            )

            with open(path) as f:
                header = json.load(f)

            env = header["env"]
            assert "python" in env
            assert "version" in env["python"]
            assert "implementation" in env["python"]
            assert "platform" in env
            assert "system" in env["platform"]
            assert "release" in env["platform"]
            assert "machine" in env["platform"]

    def test_header_contains_git_sha_field(self):
        """Test that header contains git_sha field (may be None)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path, _ = ensure_run_header(
                artifacts_dir=tmpdir,
                run_id="test-run",
                mode="test",
                pipeline_bindings_provenance={},
                policy_refs={},
            )

            with open(path) as f:
                header = json.load(f)

            assert "code" in header
            assert "git_sha" in header["code"]
            # git_sha may be None or a string depending on environment


class TestLoadRunHeader:
    """Test load_run_header() function."""

    def test_loads_existing_header(self):
        """Test loading an existing run header."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path, _ = ensure_run_header(
                artifacts_dir=tmpdir,
                run_id="test-run",
                mode="test",
                pipeline_bindings_provenance={"test": True},
                policy_refs={},
            )

            header = load_run_header(path)

            assert header["schema"] == "RunHeader.v0"
            assert header["run_id"] == "test-run"
            assert header["pipeline_bindings"] == {"test": True}

    def test_raises_for_missing_header(self):
        """Test that loading missing header raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_run_header("/nonexistent/header.json")

    def test_raises_for_invalid_schema(self):
        """Test that loading invalid schema raises ValueError."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"schema": "WrongSchema"}, f)
            f.flush()

            with pytest.raises(ValueError, match="Invalid run header schema"):
                load_run_header(f.name)


class TestVerifyRunHeader:
    """Test verify_run_header() function."""

    def test_verifies_valid_header(self):
        """Test verification of valid run header."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path, sha256 = ensure_run_header(
                artifacts_dir=tmpdir,
                run_id="test-run",
                mode="test",
                pipeline_bindings_provenance={},
                policy_refs={},
            )

            result = verify_run_header(path, sha256)

            assert result["valid"] is True
            assert result["actual_sha256"] == sha256

    def test_detects_missing_header(self):
        """Test detection of missing header file."""
        result = verify_run_header("/nonexistent/header.json", "abc123")

        assert result["valid"] is False
        assert "missing" in result["reason"].lower()

    def test_detects_hash_mismatch(self):
        """Test detection of hash mismatch."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path, _ = ensure_run_header(
                artifacts_dir=tmpdir,
                run_id="test-run",
                mode="test",
                pipeline_bindings_provenance={},
                policy_refs={},
            )

            result = verify_run_header(path, "wrong_hash")

            assert result["valid"] is False
            assert "mismatch" in result["reason"].lower()


class TestRunHeaderInTickArtifacts:
    """Test RunHeader integration with tick artifacts."""

    def test_tick_creates_run_header(self):
        """Test that abraxas_tick creates run header."""

        def run_signal(ctx):
            return {"signal": "ok"}

        def run_compress(ctx):
            return {"compress": "ok"}

        def run_overlay(ctx):
            return {"overlay": "ok"}

        with tempfile.TemporaryDirectory() as tmpdir:
            result = abraxas_tick(
                tick=0,
                run_id="header-test",
                mode="test",
                context={},
                artifacts_dir=tmpdir,
                run_signal=run_signal,
                run_compress=run_compress,
                run_overlay=run_overlay,
            )

            # Verify run_header in artifacts
            assert "run_header" in result["artifacts"]
            assert "run_header_sha256" in result["artifacts"]

            # Verify file exists
            header_path = Path(result["artifacts"]["run_header"])
            assert header_path.exists()

    def test_runindex_references_run_header(self):
        """Test that RunIndex contains run_header reference."""

        def run_signal(ctx):
            return {"signal": "ok"}

        def run_compress(ctx):
            return {"compress": "ok"}

        def run_overlay(ctx):
            return {"overlay": "ok"}

        with tempfile.TemporaryDirectory() as tmpdir:
            result = abraxas_tick(
                tick=0,
                run_id="header-test",
                mode="test",
                context={},
                artifacts_dir=tmpdir,
                run_signal=run_signal,
                run_compress=run_compress,
                run_overlay=run_overlay,
            )

            # Load RunIndex
            with open(result["artifacts"]["runindex"]) as f:
                runindex = json.load(f)

            # Verify run_header reference
            assert "run_header" in runindex["refs"]
            assert runindex["refs"]["run_header"] == result["artifacts"]["run_header"]

            # Verify run_header_sha256 in provenance
            assert "run_header_sha256" in runindex["provenance"]
            assert runindex["provenance"]["run_header_sha256"] == result["artifacts"]["run_header_sha256"]

    def test_run_header_reused_across_ticks(self):
        """Test that same run_id reuses run header across multiple ticks."""

        def run_signal(ctx):
            return {"signal": "ok"}

        def run_compress(ctx):
            return {"compress": "ok"}

        def run_overlay(ctx):
            return {"overlay": "ok"}

        with tempfile.TemporaryDirectory() as tmpdir:
            # First tick
            result1 = abraxas_tick(
                tick=0,
                run_id="multi-tick",
                mode="test",
                context={},
                artifacts_dir=tmpdir,
                run_signal=run_signal,
                run_compress=run_compress,
                run_overlay=run_overlay,
            )

            # Second tick
            result2 = abraxas_tick(
                tick=1,
                run_id="multi-tick",
                mode="test",
                context={},
                artifacts_dir=tmpdir,
                run_signal=run_signal,
                run_compress=run_compress,
                run_overlay=run_overlay,
            )

            # Run header should be same path and hash
            assert result1["artifacts"]["run_header"] == result2["artifacts"]["run_header"]
            assert result1["artifacts"]["run_header_sha256"] == result2["artifacts"]["run_header_sha256"]

    def test_run_header_contains_pipeline_bindings(self):
        """Test that run header contains pipeline bindings provenance."""

        def run_signal(ctx):
            return {"signal": "ok"}

        def run_compress(ctx):
            return {"compress": "ok"}

        def run_overlay(ctx):
            return {"overlay": "ok"}

        with tempfile.TemporaryDirectory() as tmpdir:
            result = abraxas_tick(
                tick=0,
                run_id="bindings-test",
                mode="test",
                context={},
                artifacts_dir=tmpdir,
                run_signal=run_signal,
                run_compress=run_compress,
                run_overlay=run_overlay,
            )

            # Load run header
            header = load_run_header(result["artifacts"]["run_header"])

            # Verify pipeline bindings present
            assert "pipeline_bindings" in header
            assert header["pipeline_bindings"]["bindings"] == "legacy_explicit"

    def test_run_header_contains_policy_refs(self):
        """Test that run header contains policy refs."""

        def run_signal(ctx):
            return {"signal": "ok"}

        def run_compress(ctx):
            return {"compress": "ok"}

        def run_overlay(ctx):
            return {"overlay": "ok"}

        with tempfile.TemporaryDirectory() as tmpdir:
            result = abraxas_tick(
                tick=0,
                run_id="policy-test",
                mode="test",
                context={},
                artifacts_dir=tmpdir,
                run_signal=run_signal,
                run_compress=run_compress,
                run_overlay=run_overlay,
            )

            # Load run header
            header = load_run_header(result["artifacts"]["run_header"])

            # Verify policy refs present
            assert "policy_refs" in header
            assert "retention" in header["policy_refs"]
            assert header["policy_refs"]["retention"]["schema"] == "PolicyRef.v0"


class TestRunHeaderDeterminism:
    """Test that RunHeader is deterministic where possible."""

    def test_same_inputs_produce_consistent_header(self):
        """Test that same inputs produce consistent run header structure."""
        with tempfile.TemporaryDirectory() as tmpdir1, \
             tempfile.TemporaryDirectory() as tmpdir2:

            bindings_prov = {"bindings": "test", "oracle": {"signal": "test"}}
            policy_refs = {"retention": {"schema": "PolicyRef.v0", "policy": "retention"}}

            path1, sha1 = ensure_run_header(
                artifacts_dir=tmpdir1,
                run_id="det-test",
                mode="test",
                pipeline_bindings_provenance=bindings_prov,
                policy_refs=policy_refs,
            )
            path2, sha2 = ensure_run_header(
                artifacts_dir=tmpdir2,
                run_id="det-test",
                mode="test",
                pipeline_bindings_provenance=bindings_prov,
                policy_refs=policy_refs,
            )

            # Load both headers
            header1 = load_run_header(path1)
            header2 = load_run_header(path2)

            # Pipeline bindings and policy refs should be identical
            assert header1["pipeline_bindings"] == header2["pipeline_bindings"]
            assert header1["policy_refs"] == header2["policy_refs"]
            assert header1["run_id"] == header2["run_id"]
            assert header1["mode"] == header2["mode"]

            # Note: env and git_sha may differ between environments
            # but structure should be consistent
            assert "env" in header1 and "env" in header2
            assert "code" in header1 and "code" in header2
