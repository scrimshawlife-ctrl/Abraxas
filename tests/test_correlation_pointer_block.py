from pathlib import Path

from scripts.correlation_pointer_block import build_correlation_pointer_block


def test_build_correlation_pointer_block_present_with_anchor(tmp_path: Path):
    root = tmp_path
    artifact = root / "out" / "artifact.json"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("{}", encoding="utf-8")

    block = build_correlation_pointer_block(
        root=root,
        paths=(artifact,),
        anchors=("out/ledger.jsonl#recordId=REC-1",),
    )
    assert block["correlation_pointer_state"] == "present"
    assert block["correlation_pointer_unresolved_reasons"] == []
    assert block["correlation_pointers"] == ["out/artifact.json", "out/ledger.jsonl#recordId=REC-1"]


def test_build_correlation_pointer_block_unresolved_with_missing_path(tmp_path: Path):
    root = tmp_path
    missing = root / "out" / "missing.json"
    block = build_correlation_pointer_block(root=root, paths=(missing,))

    assert block["correlation_pointer_state"] == "unresolved"
    assert block["correlation_pointers"] == []
    assert block["correlation_pointer_unresolved_reasons"] == ["artifact_missing:out/missing.json"]
