from __future__ import annotations

from pathlib import Path

from abraxas_ase.engine import run_ase


def test_keyed_determinism_same_key(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ASE_KEY", "same-key")
    items = [
        {"id":"1","source":"ap","url":"u1","published_at":"2026-01-24T00:00:00Z","title":"Winter Storm Fern hits","text":"Power grid outages in Minnesota."},
        {"id":"2","source":"reuters","url":"u2","published_at":"2026-01-24T01:00:00Z","title":"Ukraine talks in Abu Dhabi","text":"Strikes on power grid continue."},
    ]

    out1 = tmp_path / "o1"
    out2 = tmp_path / "o2"
    run_ase(items=items, date="2026-01-24", outdir=out1, pfdi_state_path=None, tier="academic")
    run_ase(items=items, date="2026-01-24", outdir=out2, pfdi_state_path=None, tier="academic")

    rep1 = (out1 / "daily_report.json").read_text(encoding="utf-8")
    rep2 = (out2 / "daily_report.json").read_text(encoding="utf-8")
    assert rep1 == rep2
