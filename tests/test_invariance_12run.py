from __future__ import annotations

from pathlib import Path

from abraxas_ase.engine import run_ase


def test_invariance_12run(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ASE_KEY", "test-key-1")
    items = [
        {"id":"1","source":"ap","url":"u1","published_at":"2026-01-24T00:00:00Z","title":"Winter Storm Fern hits","text":"Power grid outages in Minnesota."},
        {"id":"2","source":"reuters","url":"u2","published_at":"2026-01-24T01:00:00Z","title":"Ukraine talks in Abu Dhabi","text":"Strikes on power grid continue."},
    ]

    outs = []
    for n in range(12):
        outn = tmp_path / f"o{n}"
        run_ase(items=items, date="2026-01-24", outdir=outn, pfdi_state_path=None, tier="academic")
        outs.append((outn / "daily_report.json").read_text(encoding="utf-8"))

    # all identical
    assert len(set(outs)) == 1
