from __future__ import annotations

import json
from pathlib import Path

from abraxas_ase.engine import run_ase


def test_clusters_emitted(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ASE_KEY", "test-key-1")
    items = [
        {"id":"1","source":"ap","url":"u1","published_at":"2026-01-24T00:00:00Z","title":"Winter Storm Fern hits","text":"Power grid outages in Minnesota."},
        {"id":"2","source":"reuters","url":"u2","published_at":"2026-01-24T01:00:00Z","title":"Ukraine talks in Abu Dhabi","text":"Strikes on power grid continue."},
    ]
    outdir = tmp_path / "out"
    run_ase(items=items, date="2026-01-24", outdir=outdir, pfdi_state_path=None, tier="academic")

    report = json.loads((outdir / "daily_report.json").read_text(encoding="utf-8"))
    clusters = report.get("clusters", {}).get("by_item_id", {})
    assert clusters
    assert all(len(key) == 16 for key in clusters.keys())
