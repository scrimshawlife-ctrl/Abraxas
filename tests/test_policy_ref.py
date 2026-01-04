"""
Tests for PolicyRef.v0 provenance tracking.

Verifies:
- PolicyRef creation for existing/missing policies
- PolicyRef verification and drift detection
- PolicyRef embedding in artifact provenance
"""

import json
import tempfile
from pathlib import Path

import pytest

from abraxas.runtime import (
    abraxas_tick,
    ArtifactPruner,
)
from abraxas.runtime.policy_ref import (
    policy_ref_for_retention,
    policy_ref_for_file,
    verify_policy_ref,
)


class TestPolicyRefCreation:
    """Test PolicyRef creation."""

    def test_creates_ref_for_missing_policy(self):
        """Test that missing policy produces ref with present=False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ref = policy_ref_for_retention(tmpdir)

            assert ref["schema"] == "PolicyRef.v0"
            assert ref["policy"] == "retention"
            assert ref["present"] is False
            assert ref["sha256"] is None
            assert ref["path_pattern"] == "policy/retention.json"

    def test_creates_ref_for_existing_policy(self):
        """Test that existing policy produces ref with present=True and sha256."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a policy file
            pruner = ArtifactPruner(tmpdir)
            policy = pruner.load_policy()
            policy["enabled"] = True
            pruner.save_policy(policy)

            ref = policy_ref_for_retention(tmpdir)

            assert ref["schema"] == "PolicyRef.v0"
            assert ref["policy"] == "retention"
            assert ref["present"] is True
            assert ref["sha256"] is not None
            assert len(ref["sha256"]) == 64  # SHA-256 hex length

    def test_sha256_changes_with_policy_content(self):
        """Test that sha256 changes when policy content changes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pruner = ArtifactPruner(tmpdir)

            # Create initial policy
            policy = pruner.load_policy()
            pruner.save_policy(policy)
            ref1 = policy_ref_for_retention(tmpdir)

            # Modify policy
            policy["keep_last_ticks"] = 999
            pruner.save_policy(policy)
            ref2 = policy_ref_for_retention(tmpdir)

            # SHA-256 should differ
            assert ref1["sha256"] != ref2["sha256"]


class TestPolicyRefForFile:
    """Test policy_ref_for_file() function."""

    def test_creates_ref_for_arbitrary_file(self):
        """Test creating ref for an arbitrary file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"test": "data"}, f)
            f.flush()

            ref = policy_ref_for_file("custom", f.name)

            assert ref["schema"] == "PolicyRef.v0"
            assert ref["policy"] == "custom"
            assert ref["present"] is True
            assert ref["sha256"] is not None

    def test_creates_ref_for_missing_file(self):
        """Test creating ref for a missing file."""
        ref = policy_ref_for_file("custom", "/nonexistent/path.json")

        assert ref["schema"] == "PolicyRef.v0"
        assert ref["policy"] == "custom"
        assert ref["present"] is False
        assert ref["sha256"] is None


class TestVerifyPolicyRef:
    """Test PolicyRef verification."""

    def test_verifies_unchanged_policy(self):
        """Test verification of unchanged policy."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pruner = ArtifactPruner(tmpdir)
            pruner.load_policy()

            ref = policy_ref_for_retention(tmpdir)
            result = verify_policy_ref(ref, artifacts_dir=tmpdir)

            assert result["valid"] is True
            assert result["drift"] is False

    def test_detects_modified_policy(self):
        """Test detection of modified policy."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pruner = ArtifactPruner(tmpdir)
            policy = pruner.load_policy()

            # Get ref before modification
            ref = policy_ref_for_retention(tmpdir)

            # Modify policy
            policy["keep_last_ticks"] = 12345
            pruner.save_policy(policy)

            # Verify - should detect drift
            result = verify_policy_ref(ref, artifacts_dir=tmpdir)

            assert result["valid"] is True
            assert result["drift"] is True
            assert result["current_sha256"] != result["ref_sha256"]

    def test_detects_removed_policy(self):
        """Test detection of removed policy file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pruner = ArtifactPruner(tmpdir)
            pruner.load_policy()

            # Get ref while file exists
            ref = policy_ref_for_retention(tmpdir)

            # Remove the policy file
            policy_path = Path(tmpdir) / "policy" / "retention.json"
            policy_path.unlink()

            # Verify - should detect drift
            result = verify_policy_ref(ref, artifacts_dir=tmpdir)

            assert result["valid"] is True
            assert result["drift"] is True

    def test_detects_created_policy(self):
        """Test detection of newly created policy file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Get ref while file does not exist
            ref = policy_ref_for_retention(tmpdir)
            assert ref["present"] is False

            # Create the policy file
            pruner = ArtifactPruner(tmpdir)
            pruner.load_policy()

            # Verify - should detect drift
            result = verify_policy_ref(ref, artifacts_dir=tmpdir)

            assert result["valid"] is True
            assert result["drift"] is True

    def test_rejects_invalid_schema(self):
        """Test rejection of invalid PolicyRef schema."""
        result = verify_policy_ref({"schema": "WrongSchema"})

        assert result["valid"] is False
        assert "schema" in result["reason"].lower()


class TestPolicyRefInArtifacts:
    """Test PolicyRef embedding in artifacts."""

    def test_trendpack_contains_policy_ref(self):
        """Test that TrendPack provenance contains policy_ref."""

        def run_signal(ctx):
            return {"signal": "ok"}

        def run_compress(ctx):
            return {"compress": "ok"}

        def run_overlay(ctx):
            return {"overlay": "ok"}

        with tempfile.TemporaryDirectory() as tmpdir:
            result = abraxas_tick(
                tick=0,
                run_id="pol-test",
                mode="test",
                context={},
                artifacts_dir=tmpdir,
                run_signal=run_signal,
                run_compress=run_compress,
                run_overlay=run_overlay,
            )

            # Load TrendPack
            with open(result["artifacts"]["trendpack"]) as f:
                tp = json.load(f)

            # Check provenance contains policy_ref
            assert "provenance" in tp
            assert "policy_ref" in tp["provenance"]
            assert tp["provenance"]["policy_ref"]["schema"] == "PolicyRef.v0"

    def test_resultspack_contains_policy_ref(self):
        """Test that ResultsPack provenance contains policy_ref."""

        def run_signal(ctx):
            return {"signal": "ok"}

        def run_compress(ctx):
            return {"compress": "ok"}

        def run_overlay(ctx):
            return {"overlay": "ok"}

        with tempfile.TemporaryDirectory() as tmpdir:
            result = abraxas_tick(
                tick=0,
                run_id="pol-test",
                mode="test",
                context={},
                artifacts_dir=tmpdir,
                run_signal=run_signal,
                run_compress=run_compress,
                run_overlay=run_overlay,
            )

            # Load ResultsPack
            with open(result["artifacts"]["results_pack"]) as f:
                rp = json.load(f)

            # Check provenance contains policy_ref
            assert "provenance" in rp
            assert "policy_ref" in rp["provenance"]
            assert rp["provenance"]["policy_ref"]["schema"] == "PolicyRef.v0"

    def test_runindex_contains_policy_ref(self):
        """Test that RunIndex provenance contains policy_ref."""

        def run_signal(ctx):
            return {"signal": "ok"}

        def run_compress(ctx):
            return {"compress": "ok"}

        def run_overlay(ctx):
            return {"overlay": "ok"}

        with tempfile.TemporaryDirectory() as tmpdir:
            result = abraxas_tick(
                tick=0,
                run_id="pol-test",
                mode="test",
                context={},
                artifacts_dir=tmpdir,
                run_signal=run_signal,
                run_compress=run_compress,
                run_overlay=run_overlay,
            )

            # Load RunIndex
            with open(result["artifacts"]["runindex"]) as f:
                ri = json.load(f)

            # Check provenance contains policy_ref
            assert "provenance" in ri
            assert "policy_ref" in ri["provenance"]
            assert ri["provenance"]["policy_ref"]["schema"] == "PolicyRef.v0"

    def test_viewpack_contains_policy_ref(self):
        """Test that ViewPack provenance contains policy_ref."""

        def run_signal(ctx):
            return {"signal": "ok"}

        def run_compress(ctx):
            return {"compress": "ok"}

        def run_overlay(ctx):
            return {"overlay": "ok"}

        with tempfile.TemporaryDirectory() as tmpdir:
            result = abraxas_tick(
                tick=0,
                run_id="pol-test",
                mode="test",
                context={},
                artifacts_dir=tmpdir,
                run_signal=run_signal,
                run_compress=run_compress,
                run_overlay=run_overlay,
            )

            # Load ViewPack
            with open(result["artifacts"]["viewpack"]) as f:
                vp = json.load(f)

            # Check provenance contains policy_ref
            assert "provenance" in vp
            assert "policy_ref" in vp["provenance"]
            assert vp["provenance"]["policy_ref"]["schema"] == "PolicyRef.v0"


class TestPolicyRefWithRetentionPolicy:
    """Test PolicyRef when retention policy exists."""

    def test_policy_ref_tracks_existing_policy(self):
        """Test that policy_ref correctly captures existing policy hash."""

        def run_signal(ctx):
            return {"signal": "ok"}

        def run_compress(ctx):
            return {"compress": "ok"}

        def run_overlay(ctx):
            return {"overlay": "ok"}

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create and configure retention policy first
            pruner = ArtifactPruner(tmpdir)
            policy = pruner.load_policy()
            policy["enabled"] = True
            policy["keep_last_ticks"] = 100
            pruner.save_policy(policy)

            # Now create artifacts
            result = abraxas_tick(
                tick=0,
                run_id="pol-exists",
                mode="test",
                context={},
                artifacts_dir=tmpdir,
                run_signal=run_signal,
                run_compress=run_compress,
                run_overlay=run_overlay,
            )

            # Load TrendPack and check policy_ref
            with open(result["artifacts"]["trendpack"]) as f:
                tp = json.load(f)

            pol_ref = tp["provenance"]["policy_ref"]
            assert pol_ref["present"] is True
            assert pol_ref["sha256"] is not None

            # Verify the ref matches current policy
            verification = verify_policy_ref(pol_ref, artifacts_dir=tmpdir)
            assert verification["drift"] is False


class TestPolicyRefDeterminism:
    """Test that PolicyRef is deterministic."""

    def test_same_policy_produces_same_ref(self):
        """Test that same policy content produces same PolicyRef."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pruner = ArtifactPruner(tmpdir)
            pruner.load_policy()

            ref1 = policy_ref_for_retention(tmpdir)
            ref2 = policy_ref_for_retention(tmpdir)

            assert ref1["sha256"] == ref2["sha256"]
