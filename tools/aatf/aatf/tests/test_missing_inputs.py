from pathlib import Path

from aatf.ingest import ingest_file


def test_missing_file(tmp_path, monkeypatch):
    monkeypatch.setenv("AATF_HOME", str(tmp_path / ".aatf"))
    result = ingest_file(str(tmp_path / "missing.txt"), tags=[])
    assert result["status"] == "error"
    assert result["error"] == "missing_file"


def test_unsupported_format(tmp_path, monkeypatch):
    monkeypatch.setenv("AATF_HOME", str(tmp_path / ".aatf"))
    file_path = tmp_path / "sample.bin"
    file_path.write_bytes(b"binary")
    result = ingest_file(str(file_path), tags=[])
    assert result["status"] == "error"
    assert result["error"] == "unsupported_format"
