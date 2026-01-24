from __future__ import annotations

from pathlib import Path

import pytest

from abraxas_ase.engine import run_ase


def test_tier_gating_academic_requires_key(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("ASE_KEY", raising=False)
    items = [
        {"id":"1","source":"ap","url":"u1","published_at":"2026-01-24T00:00:00Z","title":"Winter Storm Fern hits","text":"Power grid outages in Minnesota."},
    ]
    outdir = tmp_path / "out"
    with pytest.raises(RuntimeError):
        run_ase(items=items, date="2026-01-24", outdir=outdir, pfdi_state_path=None, tier="academic")
