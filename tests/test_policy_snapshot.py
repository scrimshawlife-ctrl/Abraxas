"""
Tests for PolicySnapshot.v0 immutable snapshot system.

Verifies:
- Snapshot creation and content-addressing
- Snapshot reuse for same content
- Snapshot verification
- PolicyRef from snapshot creation
- Missing policy handling
"""

import json
import tempfile
from pathlib import Path

import pytest

from abraxas.runtime import (
    abraxas_tick,
    ArtifactPruner,
)
from abraxas.runtime.policy_snapshot import (
    ensure_policy_snapshot,
    policy_ref_from_snapshot,
    resolve_snapshot_path,
    load_policy_snapshot,
    verify_policy_snapshot,
)


class TestEnsurePolicySnapshot:
    """Test ensure_policy_snapshot() function."""

    def test_creates_snapshot_for_existing_policy(self):
        """Test snapshot creation for existing policy file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a policy file
            pruner = ArtifactPruner(tmpdir)
            policy = pruner.load_policy()
            policy["enabled"] = True
            policy["keep_last_ticks"] = 50
            pruner.save_policy(policy)

            policy_path = str(Path(tmpdir) / "policy" / "retention.json")
            snap_path_pattern, snap_sha = ensure_policy_snapshot(
                artifacts_dir=tmpdir,
                run_id="test-run",
                policy_name="retention",
                policy_path=policy_path,
            )

            # Verify snapshot was created (resolve relative path)
            resolved_path = resolve_snapshot_path(snap_path_pattern, tmpdir)
            assert resolved_path.exists()
            assert len(snap_sha) == 64  # SHA-256 hex length

            # Verify snapshot content
            with open(resolved_path) as f:
                snapshot = json.load(f)
            assert snapshot["schema"] == "PolicySnapshot.v0"
            assert snapshot["policy"] == "retention"
            assert snapshot["present"] is True
            assert snapshot["policy_obj"]["enabled"] is True
            assert snapshot["policy_obj"]["keep_last_ticks"] == 50

    def test_creates_snapshot_for_missing_policy(self):
        """Test snapshot creation for missing policy file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy_path = str(Path(tmpdir) / "policy" / "retention.json")
            snap_path_pattern, snap_sha = ensure_policy_snapshot(
                artifacts_dir=tmpdir,
                run_id="test-run",
                policy_name="retention",
                policy_path=policy_path,
            )

            # Verify snapshot was created (resolve relative path)
            resolved_path = resolve_snapshot_path(snap_path_pattern, tmpdir)
            assert resolved_path.exists()

            # Verify snapshot content marks policy as missing
            with open(resolved_path) as f:
                snapshot = json.load(f)
            assert snapshot["schema"] == "PolicySnapshot.v0"
            assert snapshot["present"] is False
            assert snapshot["policy_obj"] is None

    def test_snapshot_path_includes_run_id(self):
        """Test that snapshot path includes run_id for scoping."""
        with tempfile.TemporaryDirectory() as tmpdir:
            policy_path = str(Path(tmpdir) / "policy" / "nonexistent.json")
            snap_path_pattern, _ = ensure_policy_snapshot(
                artifacts_dir=tmpdir,
                run_id="my-run-id",
                policy_name="retention",
                policy_path=policy_path,
            )

            assert "policy_snapshots" in snap_path_pattern
            assert "my-run-id" in snap_path_pattern
            assert "retention." in snap_path_pattern
            assert ".policysnapshot.json" in snap_path_pattern

    def test_reuses_existing_snapshot(self):
        """Test that same content reuses existing snapshot file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a policy file
            pruner = ArtifactPruner(tmpdir)
            policy = pruner.load_policy()
            pruner.save_policy(policy)

            policy_path = str(Path(tmpdir) / "policy" / "retention.json")

            # Create snapshot twice
            snap_path1, snap_sha1 = ensure_policy_snapshot(
                artifacts_dir=tmpdir,
                run_id="test-run",
                policy_name="retention",
                policy_path=policy_path,
            )
            snap_path2, snap_sha2 = ensure_policy_snapshot(
                artifacts_dir=tmpdir,
                run_id="test-run",
                policy_name="retention",
                policy_path=policy_path,
            )

            # Should return same path and hash (content-addressed)
            assert snap_path1 == snap_path2
            assert snap_sha1 == snap_sha2

    def test_different_content_creates_different_snapshot(self):
        """Test that different content creates different snapshot."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pruner = ArtifactPruner(tmpdir)
            policy_path = str(Path(tmpdir) / "policy" / "retention.json")

            # Create first snapshot
            policy = pruner.load_policy()
            policy["keep_last_ticks"] = 10
            pruner.save_policy(policy)
            snap_path1, snap_sha1 = ensure_policy_snapshot(
                artifacts_dir=tmpdir,
                run_id="test-run",
                policy_name="retention",
                policy_path=policy_path,
            )

            # Modify policy and create second snapshot
            policy["keep_last_ticks"] = 99
            pruner.save_policy(policy)
            snap_path2, snap_sha2 = ensure_policy_snapshot(
                artifacts_dir=tmpdir,
                run_id="test-run",
                policy_name="retention",
                policy_path=policy_path,
            )

            # Should be different paths and hashes
            assert snap_path1 != snap_path2
            assert snap_sha1 != snap_sha2


class TestPolicyRefFromSnapshot:
    """Test policy_ref_from_snapshot() function."""

    def test_creates_valid_policy_ref(self):
        """Test that policy_ref_from_snapshot creates valid PolicyRef."""
        ref = policy_ref_from_snapshot(
            policy="retention",
            snapshot_path="/path/to/snapshot.json",
            snapshot_sha256="abc123",
        )

        assert ref["schema"] == "PolicyRef.v0"
        assert ref["policy"] == "retention"
        assert ref["snapshot_path"] == "/path/to/snapshot.json"
        assert ref["snapshot_sha256"] == "abc123"


class TestLoadPolicySnapshot:
    """Test load_policy_snapshot() function."""

    def test_loads_existing_snapshot(self):
        """Test loading an existing snapshot file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a policy and snapshot
            pruner = ArtifactPruner(tmpdir)
            pruner.load_policy()

            policy_path = str(Path(tmpdir) / "policy" / "retention.json")
            snap_path_pattern, _ = ensure_policy_snapshot(
                artifacts_dir=tmpdir,
                run_id="test-run",
                policy_name="retention",
                policy_path=policy_path,
            )

            # Load the snapshot (using artifacts_dir for relative path resolution)
            snapshot = load_policy_snapshot(snap_path_pattern, artifacts_dir=tmpdir)

            assert snapshot["schema"] == "PolicySnapshot.v0"
            assert snapshot["policy"] == "retention"
            assert snapshot["present"] is True

    def test_raises_for_missing_snapshot(self):
        """Test that loading missing snapshot raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_policy_snapshot("/nonexistent/snapshot.json")

    def test_raises_for_invalid_schema(self):
        """Test that loading invalid schema raises ValueError."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"schema": "WrongSchema"}, f)
            f.flush()

            with pytest.raises(ValueError, match="Invalid snapshot schema"):
                load_policy_snapshot(f.name)


class TestVerifyPolicySnapshot:
    """Test verify_policy_snapshot() function."""

    def test_verifies_valid_snapshot(self):
        """Test verification of valid snapshot."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pruner = ArtifactPruner(tmpdir)
            pruner.load_policy()

            policy_path = str(Path(tmpdir) / "policy" / "retention.json")
            snap_path_pattern, snap_sha = ensure_policy_snapshot(
                artifacts_dir=tmpdir,
                run_id="test-run",
                policy_name="retention",
                policy_path=policy_path,
            )

            result = verify_policy_snapshot(snap_path_pattern, snap_sha, artifacts_dir=tmpdir)

            assert result["valid"] is True
            assert result["actual_sha256"] == snap_sha

    def test_detects_missing_snapshot(self):
        """Test detection of missing snapshot file."""
        result = verify_policy_snapshot("/nonexistent/snapshot.json", "abc123")

        assert result["valid"] is False
        assert "missing" in result["reason"].lower()

    def test_detects_hash_mismatch(self):
        """Test detection of hash mismatch."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pruner = ArtifactPruner(tmpdir)
            pruner.load_policy()

            policy_path = str(Path(tmpdir) / "policy" / "retention.json")
            snap_path_pattern, _ = ensure_policy_snapshot(
                artifacts_dir=tmpdir,
                run_id="test-run",
                policy_name="retention",
                policy_path=policy_path,
            )

            # Verify with wrong hash
            result = verify_policy_snapshot(snap_path_pattern, "wrong_hash", artifacts_dir=tmpdir)

            assert result["valid"] is False
            assert "mismatch" in result["reason"].lower()


class TestSnapshotInTickArtifacts:
    """Test that tick artifacts use snapshot-based PolicyRef."""

    def test_tick_creates_policy_snapshot(self):
        """Test that abraxas_tick creates policy snapshot."""

        def run_signal(ctx):
            return {"signal": "ok"}

        def run_compress(ctx):
            return {"compress": "ok"}

        def run_overlay(ctx):
            return {"overlay": "ok"}

        with tempfile.TemporaryDirectory() as tmpdir:
            result = abraxas_tick(
                tick=0,
                run_id="snap-test",
                mode="test",
                context={},
                artifacts_dir=tmpdir,
                run_signal=run_signal,
                run_compress=run_compress,
                run_overlay=run_overlay,
            )

            # Verify snapshot directory was created
            snap_dir = Path(tmpdir) / "policy_snapshots" / "snap-test"
            assert snap_dir.exists()

            # Verify at least one snapshot file exists
            snapshots = list(snap_dir.glob("*.policysnapshot.json"))
            assert len(snapshots) >= 1

    def test_tick_policy_ref_points_to_snapshot(self):
        """Test that tick artifacts contain snapshot-based PolicyRef."""

        def run_signal(ctx):
            return {"signal": "ok"}

        def run_compress(ctx):
            return {"compress": "ok"}

        def run_overlay(ctx):
            return {"overlay": "ok"}

        with tempfile.TemporaryDirectory() as tmpdir:
            result = abraxas_tick(
                tick=0,
                run_id="snap-test",
                mode="test",
                context={},
                artifacts_dir=tmpdir,
                run_signal=run_signal,
                run_compress=run_compress,
                run_overlay=run_overlay,
            )

            # Load TrendPack and verify PolicyRef
            with open(result["artifacts"]["trendpack"]) as f:
                tp = json.load(f)

            pol_ref = tp["provenance"]["policy_ref"]
            assert pol_ref["schema"] == "PolicyRef.v0"
            assert "snapshot_path" in pol_ref
            assert "snapshot_sha256" in pol_ref

            # Verify the snapshot file exists (resolve relative path) and is valid
            resolved_path = resolve_snapshot_path(pol_ref["snapshot_path"], tmpdir)
            assert resolved_path.exists()
            verification = verify_policy_snapshot(
                pol_ref["snapshot_path"],
                pol_ref["snapshot_sha256"],
                artifacts_dir=tmpdir,
            )
            assert verification["valid"] is True

    def test_snapshot_is_immutable(self):
        """Test that snapshot content remains stable even if policy changes."""

        def run_signal(ctx):
            return {"signal": "ok"}

        def run_compress(ctx):
            return {"compress": "ok"}

        def run_overlay(ctx):
            return {"overlay": "ok"}

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create policy
            pruner = ArtifactPruner(tmpdir)
            policy = pruner.load_policy()
            policy["keep_last_ticks"] = 42
            pruner.save_policy(policy)

            # Run tick
            result = abraxas_tick(
                tick=0,
                run_id="immut-test",
                mode="test",
                context={},
                artifacts_dir=tmpdir,
                run_signal=run_signal,
                run_compress=run_compress,
                run_overlay=run_overlay,
            )

            # Get snapshot path
            with open(result["artifacts"]["trendpack"]) as f:
                tp = json.load(f)
            snap_path_pattern = tp["provenance"]["policy_ref"]["snapshot_path"]
            resolved_path = resolve_snapshot_path(snap_path_pattern, tmpdir)

            # Load original snapshot
            with open(resolved_path) as f:
                original_snapshot = json.load(f)
            assert original_snapshot["policy_obj"]["keep_last_ticks"] == 42

            # Modify policy
            policy["keep_last_ticks"] = 999
            pruner.save_policy(policy)

            # Snapshot should still have original value
            with open(resolved_path) as f:
                snapshot_after = json.load(f)
            assert snapshot_after["policy_obj"]["keep_last_ticks"] == 42


class TestSnapshotDeterminism:
    """Test that snapshot creation is deterministic."""

    def test_same_policy_produces_same_hash(self):
        """Test that same policy content produces same snapshot hash."""
        with tempfile.TemporaryDirectory() as tmpdir1, \
             tempfile.TemporaryDirectory() as tmpdir2:
            # Create identical policies in both dirs
            pruner1 = ArtifactPruner(tmpdir1)
            pruner2 = ArtifactPruner(tmpdir2)

            # Load default policies and update with same values
            policy1 = pruner1.load_policy()
            policy2 = pruner2.load_policy()
            policy1["enabled"] = True
            policy1["keep_last_ticks"] = 100
            policy2["enabled"] = True
            policy2["keep_last_ticks"] = 100
            pruner1.save_policy(policy1)
            pruner2.save_policy(policy2)

            policy_path1 = str(Path(tmpdir1) / "policy" / "retention.json")
            policy_path2 = str(Path(tmpdir2) / "policy" / "retention.json")

            snap_pattern1, sha1 = ensure_policy_snapshot(
                artifacts_dir=tmpdir1,
                run_id="test",
                policy_name="retention",
                policy_path=policy_path1,
            )
            snap_pattern2, sha2 = ensure_policy_snapshot(
                artifacts_dir=tmpdir2,
                run_id="test",
                policy_name="retention",
                policy_path=policy_path2,
            )

            # With portable=True (default), same content produces same hash
            # because we use relative source_path_pattern
            assert sha1 == sha2

            snap1 = load_policy_snapshot(snap_pattern1, artifacts_dir=tmpdir1)
            snap2 = load_policy_snapshot(snap_pattern2, artifacts_dir=tmpdir2)

            assert snap1["policy_obj"] == snap2["policy_obj"]
