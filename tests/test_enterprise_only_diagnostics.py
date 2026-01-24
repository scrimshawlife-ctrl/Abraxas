from __future__ import annotations

import json
from pathlib import Path

from abraxas_ase.engine import run_ase


def _items() -> list[dict]:
    return [
        {
            "id": "1",
            "source": "ap",
            "url": "u1",
            "published_at": "2026-01-24T00:00:00Z",
            "title": "Winter Storm Fern hits",
            "text": "Power grid outages in Minnesota.",
        }
    ]


def test_enterprise_only_diagnostics(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ASE_KEY", "test-key")
    enterprise_out = tmp_path / "enterprise"
    academic_out = tmp_path / "academic"

    run_ase(
        items=_items(),
        date="2026-01-24",
        outdir=enterprise_out,
        pfdi_state_path=None,
        tier="enterprise",
        enterprise_diagnostics={"promotion": {"promoted_today": 1}},
    )
    rep_ent = json.loads((enterprise_out / "daily_report.json").read_text(encoding="utf-8"))
    assert "enterprise_diagnostics" in rep_ent

    run_ase(
        items=_items(),
        date="2026-01-24",
        outdir=academic_out,
        pfdi_state_path=None,
        tier="academic",
        enterprise_diagnostics={"promotion": {"promoted_today": 1}},
    )
    rep_acad = json.loads((academic_out / "daily_report.json").read_text(encoding="utf-8"))
    assert "enterprise_diagnostics" not in rep_acad
