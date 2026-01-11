"""
Tests for abraxas.runtime.artifacts (provenance-sealed artifact emission).
"""

import tempfile
from pathlib import Path
import json

from abraxas.runtime.artifacts import ArtifactWriter, ArtifactRecord


def test_artifact_writer_basic():
    """Test basic artifact writing with SHA-256."""
    with tempfile.TemporaryDirectory() as tmpdir:
        aw = ArtifactWriter(tmpdir)

        obj = {"test": "data", "value": 42}
        rec = aw.write_json(
            run_id="TEST-001",
            tick=0,
            kind="test",
            schema="Test.v0",
            obj=obj,
            rel_path="test/TEST-001/000000.test.json",
        )

        # Verify record structure
        assert isinstance(rec, ArtifactRecord)
        assert rec.run_id == "TEST-001"
        assert rec.tick == 0
        assert rec.kind == "test"
        assert rec.schema == "Test.v0"
        assert rec.sha256 is not None
        assert rec.bytes > 0

        # Verify file was written
        path = Path(rec.path)
        assert path.exists()

        # Verify content
        with open(path) as f:
            loaded = json.load(f)
        assert loaded == obj


def test_artifact_writer_deterministic_json():
    """Test that JSON serialization is deterministic."""
    with tempfile.TemporaryDirectory() as tmpdir1, tempfile.TemporaryDirectory() as tmpdir2:
        aw1 = ArtifactWriter(tmpdir1)
        aw2 = ArtifactWriter(tmpdir2)

        obj = {"b": 2, "a": 1, "c": 3}  # Deliberately unsorted

        rec1 = aw1.write_json(
            run_id="TEST-002",
            tick=0,
            kind="test",
            schema="Test.v0",
            obj=obj,
            rel_path="test.json",
        )

        rec2 = aw2.write_json(
            run_id="TEST-002",
            tick=0,
            kind="test",
            schema="Test.v0",
            obj=obj,
            rel_path="test.json",
        )

        # Same object → same hash
        assert rec1.sha256 == rec2.sha256
        assert rec1.bytes == rec2.bytes


def test_artifact_writer_manifest_creation():
    """Test manifest ledger creation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        aw = ArtifactWriter(tmpdir)

        aw.write_json(
            run_id="TEST-003",
            tick=0,
            kind="trendpack",
            schema="TrendPack.v0",
            obj={"test": 1},
            rel_path="viz/TEST-003/000000.trendpack.json",
            extra={"mode": "test"},
        )

        # Verify manifest was created
        manifest_path = Path(tmpdir) / "manifests" / "TEST-003.manifest.json"
        assert manifest_path.exists()

        with open(manifest_path) as f:
            manifest = json.load(f)

        assert manifest["schema"] == "Manifest.v0"
        assert manifest["run_id"] == "TEST-003"
        assert len(manifest["records"]) == 1

        rec = manifest["records"][0]
        assert rec["tick"] == 0
        assert rec["kind"] == "trendpack"
        assert rec["schema"] == "TrendPack.v0"
        assert rec["sha256"] is not None
        assert rec["extra"]["mode"] == "test"


def test_artifact_writer_manifest_append():
    """Test manifest append-only behavior."""
    with tempfile.TemporaryDirectory() as tmpdir:
        aw = ArtifactWriter(tmpdir)

        # Write multiple artifacts for same run
        aw.write_json(
            run_id="TEST-004",
            tick=0,
            kind="trendpack",
            schema="TrendPack.v0",
            obj={"tick": 0},
            rel_path="viz/TEST-004/000000.trendpack.json",
        )

        aw.write_json(
            run_id="TEST-004",
            tick=0,
            kind="runindex",
            schema="RunIndex.v0",
            obj={"tick": 0},
            rel_path="run_index/TEST-004/000000.runindex.json",
        )

        aw.write_json(
            run_id="TEST-004",
            tick=1,
            kind="trendpack",
            schema="TrendPack.v0",
            obj={"tick": 1},
            rel_path="viz/TEST-004/000001.trendpack.json",
        )

        manifest_path = Path(tmpdir) / "manifests" / "TEST-004.manifest.json"
        with open(manifest_path) as f:
            manifest = json.load(f)

        assert len(manifest["records"]) == 3

        # Verify deterministic sorting: (tick, kind, schema, path)
        ticks = [r["tick"] for r in manifest["records"]]
        assert ticks == [0, 0, 1]  # Sorted by tick first


def test_artifact_writer_manifest_deterministic_sort():
    """Test manifest records are deterministically sorted."""
    with tempfile.TemporaryDirectory() as tmpdir:
        aw = ArtifactWriter(tmpdir)

        # Write in non-sequential order
        aw.write_json(
            run_id="TEST-005",
            tick=2,
            kind="trendpack",
            schema="TrendPack.v0",
            obj={"tick": 2},
            rel_path="viz/TEST-005/000002.trendpack.json",
        )

        aw.write_json(
            run_id="TEST-005",
            tick=0,
            kind="trendpack",
            schema="TrendPack.v0",
            obj={"tick": 0},
            rel_path="viz/TEST-005/000000.trendpack.json",
        )

        aw.write_json(
            run_id="TEST-005",
            tick=1,
            kind="trendpack",
            schema="TrendPack.v0",
            obj={"tick": 1},
            rel_path="viz/TEST-005/000001.trendpack.json",
        )

        manifest_path = Path(tmpdir) / "manifests" / "TEST-005.manifest.json"
        with open(manifest_path) as f:
            manifest = json.load(f)

        # Should be sorted by tick
        ticks = [r["tick"] for r in manifest["records"]]
        assert ticks == [0, 1, 2]


def test_artifact_writer_sha256_differs_on_change():
    """Test that different content produces different SHA-256."""
    with tempfile.TemporaryDirectory() as tmpdir:
        aw = ArtifactWriter(tmpdir)

        rec1 = aw.write_json(
            run_id="TEST-006",
            tick=0,
            kind="test",
            schema="Test.v0",
            obj={"value": 1},
            rel_path="test1.json",
        )

        rec2 = aw.write_json(
            run_id="TEST-006",
            tick=1,
            kind="test",
            schema="Test.v0",
            obj={"value": 2},
            rel_path="test2.json",
        )

        # Different content → different hash
        assert rec1.sha256 != rec2.sha256
