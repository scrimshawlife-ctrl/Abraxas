from __future__ import annotations

import json
from pathlib import Path

from abraxas_ase.engine import run_ase


def test_canary_words_participate_and_tagged(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ASE_KEY", "test-key-1")
    lanes = tmp_path / "lanes"
    lanes.mkdir()
    (lanes / "canary.txt").write_text("sail\n", encoding="utf-8")

    items = [
        {"id":"1","source":"ap","url":"u1","published_at":"2026-01-24T00:00:00Z","title":"Minneapolis update","text":"Minneapolis"},
    ]
    outdir = tmp_path / "out"
    run_ase(items=items, date="2026-01-24", outdir=outdir, pfdi_state_path=None, lanes_dir=lanes, tier="academic")

    rep = json.loads((outdir / "daily_report.json").read_text(encoding="utf-8"))
    hits = rep["verified_sub_anagrams"]
    assert any(h["sub"] == "sail" and h["lane"] == "canary" for h in hits)
