from __future__ import annotations

from pathlib import Path


def test_engine_invokes_runes_only() -> None:
    engine_path = Path(__file__).resolve().parents[1] / "abraxas_ase" / "engine.py"
    text = engine_path.read_text(encoding="utf-8")

    assert "invoke_rune" in text
    assert "abraxas_ase.sdct.domains" not in text
