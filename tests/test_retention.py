"""
Tests for artifact retention system.

Verifies:
- Policy loading and saving
- Tick-based pruning (keep last N)
- Byte-budget pruning
- Manifest compaction
- Deterministic ordering
"""

import json
import tempfile
from pathlib import Path

import pytest

from abraxas.runtime.retention import (
    ArtifactPruner,
    PruneReport,
    DEFAULT_POLICY,
    _parse_tick_from_name,
)
from abraxas.runtime import abraxas_tick


class TestParseTickFromName:
    """Test tick parsing from filenames."""

    def test_parses_trendpack(self):
        assert _parse_tick_from_name("000123.trendpack.json") == 123

    def test_parses_resultspack(self):
        assert _parse_tick_from_name("000000.resultspack.json") == 0

    def test_parses_runindex(self):
        assert _parse_tick_from_name("000999.runindex.json") == 999

    def test_parses_viewpack(self):
        assert _parse_tick_from_name("000042.viewpack.json") == 42

    def test_returns_none_for_invalid(self):
        assert _parse_tick_from_name("invalid.json") is None
        assert _parse_tick_from_name("no-dots") is None
        assert _parse_tick_from_name("abc.trendpack.json") is None


class TestPolicyManagement:
    """Test policy loading and saving."""

    def test_creates_default_policy(self):
        """Test that default policy is created when none exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pruner = ArtifactPruner(tmpdir)
            policy = pruner.load_policy()

            assert policy["schema"] == "RetentionPolicy.v0"
            assert policy["enabled"] is False
            assert policy["keep_last_ticks"] == 200

            # Policy file should exist
            assert (Path(tmpdir) / "policy" / "retention.json").exists()

    def test_saves_and_loads_policy(self):
        """Test policy round-trip."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pruner = ArtifactPruner(tmpdir)

            policy = pruner.load_policy()
            policy["enabled"] = True
            policy["keep_last_ticks"] = 50
            policy["max_bytes_per_run"] = 1000000

            pruner.save_policy(policy)

            # Load again
            loaded = pruner.load_policy()
            assert loaded["enabled"] is True
            assert loaded["keep_last_ticks"] == 50
            assert loaded["max_bytes_per_run"] == 1000000

    def test_rejects_invalid_schema(self):
        """Test that invalid schema raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pruner = ArtifactPruner(tmpdir)

            with pytest.raises(ValueError, match="schema"):
                pruner.save_policy({"schema": "WrongSchema"})


class TestPruneByTickCount:
    """Test pruning by tick count."""

    def _create_artifacts(self, tmpdir: str, run_id: str, ticks: list) -> None:
        """Helper to create fake artifact files for testing."""
        for tick in ticks:
            for subdir in ["viz", "results", "run_index", "view"]:
                path = Path(tmpdir) / subdir / run_id
                path.mkdir(parents=True, exist_ok=True)
                fname = f"{tick:06d}.{subdir.replace('_', '')}.json"
                (path / fname).write_text(f'{{"tick": {tick}}}')

    def test_prune_disabled_by_default(self):
        """Test that pruning does nothing when disabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self._create_artifacts(tmpdir, "test-run", [0, 1, 2, 3, 4])

            pruner = ArtifactPruner(tmpdir)
            report = pruner.prune_run("test-run")

            # Should not delete anything
            assert len(report.deleted_files) == 0
            assert report.deleted_bytes == 0

    def test_keeps_last_n_ticks(self):
        """Test that only last N ticks are kept."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create 10 ticks
            self._create_artifacts(tmpdir, "test-run", list(range(10)))

            pruner = ArtifactPruner(tmpdir)
            policy = pruner.load_policy()
            policy["enabled"] = True
            policy["keep_last_ticks"] = 3

            report = pruner.prune_run("test-run", policy=policy)

            # Should keep ticks 7, 8, 9
            assert set(report.kept_ticks) == {7, 8, 9}
            # Should delete files from ticks 0-6
            assert len(report.deleted_files) > 0

    def test_prune_with_real_tick(self):
        """Test pruning with real abraxas_tick output."""

        def run_signal(ctx):
            return {"signal": "ok"}

        def run_compress(ctx):
            return {"compress": "ok"}

        def run_overlay(ctx):
            return {"overlay": "ok"}

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create several ticks
            for tick in range(5):
                abraxas_tick(
                    tick=tick,
                    run_id="real-test",
                    mode="test",
                    context={},
                    artifacts_dir=tmpdir,
                    run_signal=run_signal,
                    run_compress=run_compress,
                    run_overlay=run_overlay,
                )

            pruner = ArtifactPruner(tmpdir)
            policy = pruner.load_policy()
            policy["enabled"] = True
            policy["keep_last_ticks"] = 2

            report = pruner.prune_run("real-test", policy=policy)

            # Should keep ticks 3, 4
            assert set(report.kept_ticks) == {3, 4}
            # Should have deleted files
            assert len(report.deleted_files) > 0


class TestPruneByBytesBudget:
    """Test pruning by bytes budget."""

    def _create_sized_artifacts(
        self, tmpdir: str, run_id: str, tick: int, size_bytes: int
    ) -> None:
        """Create artifact with specific size."""
        for subdir in ["viz", "results", "run_index", "view"]:
            path = Path(tmpdir) / subdir / run_id
            path.mkdir(parents=True, exist_ok=True)
            fname = f"{tick:06d}.{subdir.replace('_', '')}.json"
            # Create file with padding to reach target size
            content = "x" * size_bytes
            (path / fname).write_text(content)

    def test_prune_exceeds_byte_budget(self):
        """Test that files are pruned when exceeding byte budget."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create 5 ticks, each ~1000 bytes per artifact type
            for tick in range(5):
                self._create_sized_artifacts(tmpdir, "test-run", tick, 1000)

            pruner = ArtifactPruner(tmpdir)
            policy = pruner.load_policy()
            policy["enabled"] = True
            policy["keep_last_ticks"] = 10  # High enough to not trigger tick-based pruning
            policy["max_bytes_per_run"] = 10000  # ~10KB cap

            # Total is ~20KB (5 ticks * 4 artifacts * 1KB), so should prune oldest

            report = pruner.prune_run("test-run", policy=policy)

            # Should have deleted some files to get under budget
            assert report.deleted_bytes > 0


class TestDiscoverRunIds:
    """Test run_id discovery."""

    def test_discovers_multiple_runs(self):
        """Test discovery of multiple run_ids."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create artifacts for multiple runs
            for run_id in ["run-a", "run-b", "run-c"]:
                for subdir in ["viz", "results"]:
                    path = Path(tmpdir) / subdir / run_id
                    path.mkdir(parents=True, exist_ok=True)
                    (path / "000000.test.json").write_text("{}")

            pruner = ArtifactPruner(tmpdir)
            run_ids = pruner.discover_run_ids()

            assert set(run_ids) == {"run-a", "run-b", "run-c"}

    def test_discovers_empty_on_new_dir(self):
        """Test that empty directory has no run_ids."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pruner = ArtifactPruner(tmpdir)
            run_ids = pruner.discover_run_ids()
            assert run_ids == []


class TestPruneAll:
    """Test pruning all runs."""

    def test_prunes_all_runs(self):
        """Test that prune_all processes all run_ids."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create artifacts for multiple runs with many ticks
            for run_id in ["run-a", "run-b"]:
                for tick in range(10):
                    for subdir in ["viz", "results"]:
                        path = Path(tmpdir) / subdir / run_id
                        path.mkdir(parents=True, exist_ok=True)
                        (path / f"{tick:06d}.test.json").write_text("{}")

            pruner = ArtifactPruner(tmpdir)
            policy = pruner.load_policy()
            policy["enabled"] = True
            policy["keep_last_ticks"] = 3

            reports = pruner.prune_all(policy=policy)

            assert len(reports) == 2
            for report in reports:
                assert len(report.kept_ticks) == 3


class TestGetRunStats:
    """Test run statistics."""

    def test_gets_stats_for_run(self):
        """Test getting stats for a run."""

        def run_signal(ctx):
            return {"signal": "ok"}

        def run_compress(ctx):
            return {"compress": "ok"}

        def run_overlay(ctx):
            return {"overlay": "ok"}

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create several ticks
            for tick in range(3):
                abraxas_tick(
                    tick=tick,
                    run_id="stats-test",
                    mode="test",
                    context={},
                    artifacts_dir=tmpdir,
                    run_signal=run_signal,
                    run_compress=run_compress,
                    run_overlay=run_overlay,
                )

            pruner = ArtifactPruner(tmpdir)
            stats = pruner.get_run_stats("stats-test")

            assert stats["run_id"] == "stats-test"
            assert stats["tick_count"] == 3
            assert stats["file_count"] == 12  # 3 ticks * 4 artifact types
            assert stats["total_bytes"] > 0
            assert stats["oldest_tick"] == 0
            assert stats["newest_tick"] == 2


class TestManifestCompaction:
    """Test manifest compaction."""

    def test_compacts_manifest_after_prune(self):
        """Test that manifest is compacted after pruning."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a manifest with records
            manifest_dir = Path(tmpdir) / "manifests"
            manifest_dir.mkdir(parents=True, exist_ok=True)

            # Create some artifact files
            for tick in range(5):
                path = Path(tmpdir) / "viz" / "test-run"
                path.mkdir(parents=True, exist_ok=True)
                (path / f"{tick:06d}.trendpack.json").write_text("{}")

            # Create manifest with all records
            records = []
            for tick in range(5):
                records.append({
                    "tick": tick,
                    "kind": "trendpack",
                    "schema": "TrendPack.v0",
                    "path": str(Path(tmpdir) / "viz" / "test-run" / f"{tick:06d}.trendpack.json"),
                })

            manifest = {"schema": "Manifest.v0", "records": records}
            (manifest_dir / "test-run.manifest.json").write_text(
                json.dumps(manifest, sort_keys=True)
            )

            # Prune (keep last 2)
            pruner = ArtifactPruner(tmpdir)
            policy = pruner.load_policy()
            policy["enabled"] = True
            policy["keep_last_ticks"] = 2
            policy["compact_manifest"] = True

            pruner.prune_run("test-run", policy=policy)

            # Load compacted manifest
            compacted = json.loads(
                (manifest_dir / "test-run.manifest.json").read_text()
            )

            # Should only have 2 records (for kept ticks)
            assert len(compacted["records"]) == 2


class TestProtectedRoots:
    """Test that protected roots are never deleted."""

    def test_never_deletes_manifests(self):
        """Test that manifests directory is never deleted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create manifests directory with content
            manifest_dir = Path(tmpdir) / "manifests"
            manifest_dir.mkdir(parents=True, exist_ok=True)
            (manifest_dir / "test.json").write_text("{}")

            # Create artifacts to prune
            for tick in range(10):
                path = Path(tmpdir) / "viz" / "test-run"
                path.mkdir(parents=True, exist_ok=True)
                (path / f"{tick:06d}.trendpack.json").write_text("{}")

            pruner = ArtifactPruner(tmpdir)
            policy = pruner.load_policy()
            policy["enabled"] = True
            policy["keep_last_ticks"] = 1

            pruner.prune_run("test-run", policy=policy)

            # Manifests should still exist
            assert (manifest_dir / "test.json").exists()

    def test_never_deletes_policy(self):
        """Test that policy directory is never deleted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pruner = ArtifactPruner(tmpdir)
            policy = pruner.load_policy()
            policy["enabled"] = True

            pruner.save_policy(policy)

            # Policy should exist
            assert (Path(tmpdir) / "policy" / "retention.json").exists()

            # Create and prune artifacts
            for tick in range(10):
                path = Path(tmpdir) / "viz" / "test-run"
                path.mkdir(parents=True, exist_ok=True)
                (path / f"{tick:06d}.trendpack.json").write_text("{}")

            pruner.prune_run("test-run", policy=policy)

            # Policy should still exist
            assert (Path(tmpdir) / "policy" / "retention.json").exists()


class TestDeterminism:
    """Test that pruning is deterministic."""

    def test_prune_order_is_deterministic(self):
        """Test that same inputs produce same prune order."""
        with tempfile.TemporaryDirectory() as tmpdir1, \
             tempfile.TemporaryDirectory() as tmpdir2:

            # Create identical artifacts in both directories
            for tmpdir in [tmpdir1, tmpdir2]:
                for tick in range(10):
                    for subdir in ["viz", "results"]:
                        path = Path(tmpdir) / subdir / "det-test"
                        path.mkdir(parents=True, exist_ok=True)
                        (path / f"{tick:06d}.test.json").write_text(f'{{"tick":{tick}}}')

            pruner1 = ArtifactPruner(tmpdir1)
            pruner2 = ArtifactPruner(tmpdir2)

            policy = dict(DEFAULT_POLICY)
            policy["enabled"] = True
            policy["keep_last_ticks"] = 3

            report1 = pruner1.prune_run("det-test", policy=policy)
            report2 = pruner2.prune_run("det-test", policy=policy)

            # Same ticks should be kept
            assert report1.kept_ticks == report2.kept_ticks

            # Same number of files deleted
            assert len(report1.deleted_files) == len(report2.deleted_files)
