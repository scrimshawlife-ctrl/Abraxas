from __future__ import annotations

import json
from pathlib import Path

from abraxas_ase.engine import run_ase


def test_tier_gating_psychonaut(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("ASE_KEY", raising=False)
    items = [
        {"id":"1","source":"ap","url":"u1","published_at":"2026-01-24T00:00:00Z","title":"Winter Storm Fern hits","text":"Power grid outages in Minnesota."},
    ]
    outdir = tmp_path / "out"
    run_ase(items=items, date="2026-01-24", outdir=outdir, pfdi_state_path=None, tier="psychonaut")

    report = json.loads((outdir / "daily_report.json").read_text(encoding="utf-8"))
    assert "verified_sub_anagrams" not in report
    assert "clusters" not in report
    assert "pfdi_alerts" not in report
    assert "stats" in report
