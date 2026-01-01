from __future__ import annotations

from pathlib import Path

from abx.codex.registry import build_codex


def test_bell_constraint_entry_and_rune_load_deterministically():
    root = Path(__file__).resolve().parents[1] / "abx" / "codex"
    codex = build_codex(root)

    assert "CANON_BELL_CONSTRAINT" in codex.canon
    assert "ABX_BELL_CONSTRAINT" in codex.runes

    entry = codex.canon["CANON_BELL_CONSTRAINT"]
    rune = codex.runes["ABX_BELL_CONSTRAINT"]

    # Provenance hashes must be present and stable
    assert entry.provenance.content_sha256 and len(entry.provenance.content_sha256) == 64
    assert rune.provenance.content_sha256 and len(rune.provenance.content_sha256) == 64

    # Canon linkage must be correct
    assert "CANON_BELL_CONSTRAINT" in rune.canon_refs

    # Mode integrity
    assert set(entry.modes) == {"OPEN", "ALIGN", "ASCEND", "CLEAR", "SEAL"}
    assert all(k in entry.body for k in entry.modes)
