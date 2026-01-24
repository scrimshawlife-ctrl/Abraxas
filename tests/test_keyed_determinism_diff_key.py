from __future__ import annotations

import json
from pathlib import Path

from abraxas_ase.engine import run_ase


def _run_with_key(tmp_path: Path, key: str) -> dict:
    import os

    os.environ["ASE_KEY"] = key
    items = [
        {"id":"1","source":"ap","url":"u1","published_at":"2026-01-24T00:00:00Z","title":"Winter Storm Fern hits","text":"Power grid outages in Minnesota."},
        {"id":"2","source":"reuters","url":"u2","published_at":"2026-01-24T01:00:00Z","title":"Ukraine talks in Abu Dhabi","text":"Strikes on power grid continue."},
    ]
    outdir = tmp_path / key
    run_ase(items=items, date="2026-01-24", outdir=outdir, pfdi_state_path=None, tier="academic")
    return json.loads((outdir / "daily_report.json").read_text(encoding="utf-8"))


def test_keyed_identifiers_change_across_keys(tmp_path: Path) -> None:
    rep1 = _run_with_key(tmp_path, "key-one")
    rep2 = _run_with_key(tmp_path, "key-two")

    assert rep1["stats"] == rep2["stats"]
    assert rep1["run_id"] != rep2["run_id"]
    assert rep1["clusters"]["by_item_id"] != rep2["clusters"]["by_item_id"]
