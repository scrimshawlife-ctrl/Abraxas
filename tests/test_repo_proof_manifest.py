import hashlib
from pathlib import Path

from abraxas.proof.repo_hash_manifest import build_outputs, canonical_json, compute_manifest


def _write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def test_stable_sorting_sha_and_excludes(tmp_path: Path):
    _write(tmp_path / "b.txt", "b")
    _write(tmp_path / "a.txt", "a")
    _write(tmp_path / ".git" / "x", "skip")
    manifest = compute_manifest(tmp_path)
    paths = [f["path"] for f in manifest["files"]]
    assert paths == ["a.txt", "b.txt"]
    assert manifest["files"][0]["sha256"] == hashlib.sha256(b"a").hexdigest()


def test_patch_extraction_path_and_markdown(tmp_path: Path):
    _write(tmp_path / "docs" / "PATCH-069-note.md", "no heading")
    _write(tmp_path / "docs" / "x.md", "# Title\nPATCH-070 hello")
    manifest = compute_manifest(tmp_path)
    by_path = {f["path"]: f for f in manifest["files"]}
    assert by_path["docs/PATCH-069-note.md"]["patch_id"] == "PATCH-069"
    assert by_path["docs/x.md"]["patch_id"] == "PATCH-070"


def test_canonical_json_sorted_keys_and_newline():
    s = canonical_json({"b": 1, "a": 2})
    assert s == '{"a":2,"b":1}\n'


def test_drift_classes(tmp_path: Path):
    _write(tmp_path / "docs" / "PATCH-069-a.md", "a")
    outputs = build_outputs(tmp_path, "PATCH-067+")
    assert outputs["repo_canon_alignment_report.latest.json"]["drift_class"] == "repo_ahead"
    assert build_outputs(tmp_path, "PATCH-069")["repo_canon_alignment_report.latest.json"]["drift_class"] == "aligned"
    assert build_outputs(tmp_path, "PATCH-070")["repo_canon_alignment_report.latest.json"]["drift_class"] == "notion_ahead"
    assert build_outputs(tmp_path, "invalid")["repo_canon_alignment_report.latest.json"]["drift_class"] == "not_computable"


def test_repeatable_output_and_authority_flags(tmp_path: Path):
    _write(tmp_path / "docs" / "PATCH-069-a.md", "a")
    out1 = build_outputs(tmp_path, "PATCH-067+")
    out2 = build_outputs(tmp_path, "PATCH-067+")
    assert canonical_json(out1["repo_proof_manifest.latest.json"]) == canonical_json(out2["repo_proof_manifest.latest.json"])
    receipt = out1["repo_proof_receipt.latest.json"]
    assert receipt["runtime_mutation"] is False
    assert receipt["promotion_granted"] is False
    assert receipt["scheduler_write"] is False
    assert receipt["source_weight_mutation"] is False
    assert receipt["activation_allowed"] is False
