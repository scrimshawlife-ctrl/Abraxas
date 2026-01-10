import hashlib
import os
from pathlib import Path

from aatf.export.bundle import export_bundle
from aatf.ingest import ingest_file
from aatf.queue.review import apply_review
from aatf.queue.states import QueueState
from aatf.storage import load_blob


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_deterministic_ingest(tmp_path, monkeypatch):
    monkeypatch.setenv("AATF_HOME", str(tmp_path / ".aatf"))
    source = tmp_path / "sample.txt"
    source.write_text("Deterministic input", encoding="utf-8")

    first = ingest_file(str(source), tags=["alpha"])
    second = ingest_file(str(source), tags=["alpha"])

    assert first["source_hash"] == second["source_hash"]
    assert first["chunk_ids"] == second["chunk_ids"]


def test_deterministic_export_bundle(tmp_path, monkeypatch):
    monkeypatch.setenv("AATF_HOME", str(tmp_path / ".aatf"))
    source = tmp_path / "sample.txt"
    source.write_text("Deterministic export", encoding="utf-8")

    result = ingest_file(str(source), tags=["beta"])
    apply_review(result["item_id"], QueueState.APPROVED, "ok")

    first_bundle = export_bundle(["aalmanac"])
    first_hash = _hash_file(Path(first_bundle["zip_path"]))

    second_bundle = export_bundle(["aalmanac"])
    second_hash = _hash_file(Path(second_bundle["zip_path"]))

    assert first_hash == second_hash
